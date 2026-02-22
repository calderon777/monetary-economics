import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


TARGET_BASE = os.getenv("ACESTEP_TARGET_BASE", "http://127.0.0.1:8001").rstrip("/")
ALLOWED_ORIGINS = _csv_env(
    "PROXY_ALLOWED_ORIGINS",
    "https://calderon777.github.io,http://localhost,http://127.0.0.1",
)
SHARED_TOKEN = os.getenv("PROXY_SHARED_TOKEN", "").strip()
REQUIRE_TOKEN = _bool_env("PROXY_REQUIRE_TOKEN", False) and bool(SHARED_TOKEN)
REQUEST_TIMEOUT = float(os.getenv("PROXY_REQUEST_TIMEOUT_SECONDS", "600"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("PROXY_RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("PROXY_RATE_LIMIT_MAX_REQUESTS", "30"))


@dataclass
class RateBucket:
    hits: deque


_rate_buckets: dict[str, RateBucket] = defaultdict(lambda: RateBucket(hits=deque()))


app = FastAPI(title="ACE-Step Browser Proxy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Proxy-Token"],
)


_http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _client_ip(request: Request) -> str:
    # If you are behind Nginx/Caddy, configure it to set X-Forwarded-For.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(request: Request) -> None:
    ip = _client_ip(request)
    now = time.time()
    bucket = _rate_buckets[ip]

    while bucket.hits and now - bucket.hits[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.hits.popleft()

    if len(bucket.hits) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded: max {RATE_LIMIT_MAX_REQUESTS} requests "
                f"per {RATE_LIMIT_WINDOW_SECONDS} seconds."
            ),
        )

    bucket.hits.append(now)


def _require_token_if_enabled(x_proxy_token: str | None) -> None:
    if not REQUIRE_TOKEN:
        return
    if not x_proxy_token or x_proxy_token != SHARED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Proxy-Token")


def _safe_outgoing_headers(incoming: Iterable[tuple[str, str]]) -> dict[str, str]:
    blocked = {
        "host",
        "origin",
        "content-length",
        "connection",
        "accept-encoding",
        "x-proxy-token",
    }
    headers: dict[str, str] = {}
    for key, value in incoming:
        if key.lower() in blocked:
            continue
        headers[key] = value
    return headers


def _safe_response_headers(upstream_headers: httpx.Headers) -> dict[str, str]:
    keep = {
        "content-type",
        "content-length",
        "cache-control",
        "etag",
        "last-modified",
        "accept-ranges",
        "content-disposition",
    }
    return {k: v for k, v in upstream_headers.items() if k.lower() in keep}


@app.get("/healthz")
async def healthz() -> dict:
    return {
        "ok": True,
        "target_base": TARGET_BASE,
        "require_token": REQUIRE_TOKEN,
        "allowed_origins": ALLOWED_ORIGINS,
    }


@app.get("/health")
@app.get("/acestep/health")
async def proxy_health(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    assert _http_client is not None
    try:
        upstream = await _http_client.get(f"{TARGET_BASE}/health")
        return JSONResponse(
            status_code=upstream.status_code,
            content=upstream.json(),
            headers=_safe_response_headers(upstream.headers),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream ACE-Step unreachable: {exc}") from exc


@app.post("/release_task")
@app.post("/acestep/release_task")
async def proxy_release_task(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    assert _http_client is not None
    body = await request.body()
    headers = _safe_outgoing_headers(request.headers.items())
    try:
        upstream = await _http_client.post(f"{TARGET_BASE}/release_task", content=body, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream ACE-Step unreachable: {exc}") from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_safe_response_headers(upstream.headers),
    )


@app.post("/query_result")
@app.post("/acestep/query_result")
async def proxy_query_result(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    assert _http_client is not None
    body = await request.body()
    headers = _safe_outgoing_headers(request.headers.items())
    try:
        upstream = await _http_client.post(f"{TARGET_BASE}/query_result", content=body, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream ACE-Step unreachable: {exc}") from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_safe_response_headers(upstream.headers),
    )


@app.get("/v1/audio")
@app.get("/acestep/v1/audio")
async def proxy_audio(
    request: Request,
    path: str,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    assert _http_client is not None
    try:
        upstream = await _http_client.get(
            f"{TARGET_BASE}/v1/audio",
            params={"path": path},
            headers=_safe_outgoing_headers(request.headers.items()),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream ACE-Step unreachable: {exc}") from exc

    return StreamingResponse(
        iter([upstream.content]),
        status_code=upstream.status_code,
        headers=_safe_response_headers(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )
