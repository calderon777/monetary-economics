import os
import re
import time
from datetime import datetime, timezone
from hashlib import sha1
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Iterable

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field


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
TOPIC2_MAX_LYRICS_WORDS = int(os.getenv("TOPIC2_MAX_LYRICS_WORDS", "120"))
TOPIC2_MAX_LYRICS_CHARS = int(os.getenv("TOPIC2_MAX_LYRICS_CHARS", "800"))
TOPIC2_MAX_PROMPT_WORDS = int(os.getenv("TOPIC2_MAX_PROMPT_WORDS", "20"))
TOPIC2_MAX_PROMPT_CHARS = int(os.getenv("TOPIC2_MAX_PROMPT_CHARS", "140"))
TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK = int(os.getenv("TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK", "5"))
TOPIC2_ENABLE_GOOGLE_SHEETS = _bool_env("TOPIC2_ENABLE_GOOGLE_SHEETS", False)
TOPIC2_GOOGLE_SHEETS_WORKBOOK = os.getenv("TOPIC2_GOOGLE_SHEETS_WORKBOOK", "").strip()


@dataclass
class RateBucket:
    hits: deque


_rate_buckets: dict[str, RateBucket] = defaultdict(lambda: RateBucket(hits=deque()))
_topic2_submissions: list[dict[str, Any]] = []
_topic2_votes_by_submission: dict[str, set[str]] = defaultdict(set)
_topic2_score_counts_by_nickname: dict[str, int] = defaultdict(int)


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_words(text: str) -> int:
    text = (text or "").strip()
    return len(re.findall(r"\S+", text)) if text else 0


def _nickname_key(nickname: str) -> str:
    return (nickname or "").strip().lower()


def _topic_keywords(text: str) -> set[str]:
    lower = (text or "").lower()
    keywords = {
        "inflation",
        "money demand",
        "money",
        "velocity",
        "quantity theory",
        "quantity",
        "interest",
        "interest rate",
        "prices",
        "price level",
        "policy",
        "liquidity",
        "cash balances",
    }
    found: set[str] = set()
    for kw in keywords:
        if kw in lower:
            found.add(kw)
    return found


def _score_topic2_submission(payload: "Topic2SubmitScoreRequest", previous_submission: dict[str, Any] | None) -> dict[str, Any]:
    lyrics = payload.lyrics.strip()
    prompt = payload.prompt.strip()
    lyrics_words = _count_words(lyrics)
    prompt_words = _count_words(prompt)
    keywords = _topic_keywords(lyrics)

    score_correctness = 4
    if keywords:
        score_correctness += 2
    if re.search(r"\b(because|therefore|so that|leads to|causes)\b", lyrics, re.I):
        score_correctness += 1
    if re.search(r"\b(printing money\b.*\b(inflation|prices))|(\binflation\b.*\bmoney)\b", lyrics, re.I):
        score_correctness += 1

    score_concept_use = min(10, 2 + len(keywords))
    score_causal = 3 + (2 if re.search(r"\b(because|leads to|causes|therefore|if)\b", lyrics, re.I) else 0)
    score_causal += 1 if len(keywords) >= 2 else 0
    score_comm = 3 + (2 if 20 <= lyrics_words <= TOPIC2_MAX_LYRICS_WORDS else 0)
    score_comm += 1 if prompt_words > 0 else 0

    score_revision = 5
    revision_type = "none"
    if previous_submission:
        prev_lyrics = str(previous_submission.get("lyrics", "")).strip()
        if prev_lyrics and prev_lyrics != lyrics:
            prev_keywords = _topic_keywords(prev_lyrics)
            if keywords != prev_keywords or len(keywords) > len(prev_keywords):
                score_revision = 7
                revision_type = "conceptual"
            else:
                score_revision = 6
                revision_type = "surface"
        elif prev_lyrics == lyrics:
            score_revision = 4

    criteria = [
        ("economic_correctness", "Economic Correctness", max(1, min(10, score_correctness)),
         "Checks whether the economic claims appear accurate and on-topic."),
        ("concept_use", "Concept Use", max(1, min(10, score_concept_use)),
         "Looks for meaningful use of Topic 2 concepts rather than name-dropping."),
        ("causal_reasoning", "Causal Reasoning", max(1, min(10, score_causal)),
         "Looks for clear cause-and-effect links in the explanation."),
        ("communication_quality", "Communication Quality", max(1, min(10, score_comm)),
         "Checks whether the message is clear, understandable, and memorable."),
        ("revision_quality", "Revision Quality", max(1, min(10, score_revision)),
         "Compares this submission with the same nickname's previous version."),
    ]
    average = round(sum(item[2] for item in criteria) / len(criteria), 2)

    unreliable_reasons: list[str] = []
    if lyrics_words < 12:
        unreliable_reasons.append("Lyrics are very short, so scoring may not reflect real understanding.")
    if not keywords:
        unreliable_reasons.append("No clear Topic 2 keywords detected in the lyrics.")
    if payload.generated_output_metadata is None:
        unreliable_reasons.append("No generation metadata attached (acceptable for drafting, but evidence is incomplete).")

    return {
        "criteria": [
            {
                "id": cid,
                "label": label,
                "score": score,
                "feedback": feedback,
            }
            for cid, label, score, feedback in criteria
        ],
        "average_score": average,
        "unreliable_warning": bool(unreliable_reasons),
        "unreliable_reasons": unreliable_reasons,
        "revision_type": revision_type,
        "detected_topic_keywords": sorted(keywords),
    }


def _find_previous_submission(nickname: str, current_submission_id: str | None = None) -> dict[str, Any] | None:
    key = _nickname_key(nickname)
    for item in reversed(_topic2_submissions):
        if _nickname_key(str(item.get("nickname", ""))) != key:
            continue
        if current_submission_id and item.get("submission_id") == current_submission_id:
            continue
        return item
    return None


def _cohort_analytics() -> dict[str, Any]:
    if not _topic2_submissions:
        return {
            "submission_count": 0,
            "common_misconceptions": [],
            "concept_inaccuracy_patterns": [],
            "revision_type_counts": {"none": 0, "surface": 0, "conceptual": 0},
            "ai_over_reliance_indicators": [],
        }

    misconceptions: dict[str, int] = defaultdict(int)
    inaccuracy_patterns: dict[str, int] = defaultdict(int)
    revision_types: dict[str, int] = defaultdict(int)
    over_reliance: dict[str, int] = defaultdict(int)

    for sub in _topic2_submissions:
        lyrics = str(sub.get("lyrics", ""))
        score = sub.get("auto_score", {})
        rev_type = str(score.get("revision_type", "none"))
        revision_types[rev_type] += 1

        if "printing money" in lyrics.lower() and "always" in lyrics.lower():
            misconceptions["Inflation framed as automatic/always outcome without conditions"] += 1
        if "inflation" in lyrics.lower() and "interest" not in lyrics.lower() and "money demand" not in lyrics.lower():
            inaccuracy_patterns["Inflation mentioned without broader monetary transmission context"] += 1
        if score.get("average_score", 0) < 5 and len(str(lyrics).split()) < 20:
            over_reliance["Very short lyrics with low score (possible low-effort prompting)"] += 1
        if len(set(re.findall(r"\b\w+\b", lyrics.lower()))) < 12 and len(lyrics.split()) > 25:
            over_reliance["Repetitive phrasing (possible generic AI-style output)"] += 1

    def _top_items(counter: dict[str, int]) -> list[dict[str, Any]]:
        return [{"label": k, "count": v} for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]

    return {
        "submission_count": len(_topic2_submissions),
        "common_misconceptions": _top_items(misconceptions),
        "concept_inaccuracy_patterns": _top_items(inaccuracy_patterns),
        "revision_type_counts": {
            "none": revision_types.get("none", 0),
            "surface": revision_types.get("surface", 0),
            "conceptual": revision_types.get("conceptual", 0),
        },
        "ai_over_reliance_indicators": _top_items(over_reliance),
    }


class Topic2GeneratedOutputMetadata(BaseModel):
    task_id: str | None = None
    audio_url: str | None = None
    audio_duration_seconds: int | None = None
    inference_steps: int | None = None
    generation_attempt_number: int | None = None
    api_base: str | None = None


class Topic2SubmitScoreRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=30)
    lyrics: str = Field(..., min_length=1, max_length=TOPIC2_MAX_LYRICS_CHARS)
    prompt: str = Field(..., min_length=1, max_length=TOPIC2_MAX_PROMPT_CHARS)
    client_timestamp: str | None = None
    generated_output_metadata: Topic2GeneratedOutputMetadata | None = None
    publish_to_community: bool = False


class Topic2VoteRequest(BaseModel):
    voter_nickname: str = Field(..., min_length=1, max_length=30)
    submission_id: str = Field(..., min_length=6, max_length=80)


def _google_sheets_export_preview(submission: dict[str, Any]) -> dict[str, Any]:
    auto = submission.get("auto_score", {})
    criteria = {c["id"]: c["score"] for c in auto.get("criteria", [])}
    return {
        "workbook_enabled": TOPIC2_ENABLE_GOOGLE_SHEETS,
        "workbook_name": TOPIC2_GOOGLE_SHEETS_WORKBOOK or None,
        "tabs": {
            "submissions": {
                "submitted_at_utc": submission.get("submitted_at_utc"),
                "nickname": submission.get("nickname"),
                "submission_id": submission.get("submission_id"),
                "lyrics": submission.get("lyrics"),
                "prompt": submission.get("prompt"),
                "client_timestamp": submission.get("client_timestamp"),
                "publish_to_community": submission.get("publish_to_community"),
                "generated_output_metadata_json": submission.get("generated_output_metadata"),
            },
            "scores": {
                "submission_id": submission.get("submission_id"),
                "nickname": submission.get("nickname"),
                "average_score": auto.get("average_score"),
                "economic_correctness": criteria.get("economic_correctness"),
                "concept_use": criteria.get("concept_use"),
                "causal_reasoning": criteria.get("causal_reasoning"),
                "communication_quality": criteria.get("communication_quality"),
                "revision_quality": criteria.get("revision_quality"),
                "unreliable_warning": auto.get("unreliable_warning"),
                "unreliable_reasons": "; ".join(auto.get("unreliable_reasons", [])),
                "revision_type": auto.get("revision_type"),
            },
        },
    }


def _pydantic_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError("Unsupported model type for serialization")


@app.get("/healthz")
async def healthz() -> dict:
    return {
        "ok": True,
        "target_base": TARGET_BASE,
        "require_token": REQUIRE_TOKEN,
        "allowed_origins": ALLOWED_ORIGINS,
        "topic2_pilot": {
            "lyrics_word_limit": TOPIC2_MAX_LYRICS_WORDS,
            "prompt_word_limit": TOPIC2_MAX_PROMPT_WORDS,
            "max_scoring_submissions_per_nickname": TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK,
            "google_sheets_enabled": TOPIC2_ENABLE_GOOGLE_SHEETS,
            "google_sheets_workbook": TOPIC2_GOOGLE_SHEETS_WORKBOOK or None,
        },
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


@app.post("/topic2/submit-score")
async def topic2_submit_score(
    payload: Topic2SubmitScoreRequest,
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)

    lyrics_words = _count_words(payload.lyrics)
    prompt_words = _count_words(payload.prompt)
    if lyrics_words > TOPIC2_MAX_LYRICS_WORDS:
        raise HTTPException(status_code=400, detail=f"Lyrics exceed {TOPIC2_MAX_LYRICS_WORDS} words.")
    if prompt_words > TOPIC2_MAX_PROMPT_WORDS:
        raise HTTPException(status_code=400, detail=f"Prompt exceeds {TOPIC2_MAX_PROMPT_WORDS} words.")

    nick_key = _nickname_key(payload.nickname)
    if _topic2_score_counts_by_nickname[nick_key] >= TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK:
        raise HTTPException(
            status_code=429,
            detail=f"Scoring limit reached for nickname '{payload.nickname}' ({TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK} submissions).",
        )

    seed = f"{payload.nickname}|{payload.lyrics}|{payload.prompt}|{time.time_ns()}".encode("utf-8")
    submission_id = f"t2_{sha1(seed).hexdigest()[:12]}"
    previous = _find_previous_submission(payload.nickname)
    auto_score = _score_topic2_submission(payload, previous)

    submission = {
        "submission_id": submission_id,
        "topic": "topic2ludic",
        "nickname": payload.nickname.strip(),
        "lyrics": payload.lyrics.strip(),
        "prompt": payload.prompt.strip(),
        "lyrics_word_count": lyrics_words,
        "prompt_word_count": prompt_words,
        "client_timestamp": payload.client_timestamp,
        "submitted_at_utc": _utc_now_iso(),
        "submitted_by_ip": _client_ip(request),
        "publish_to_community": payload.publish_to_community,
        "generated_output_metadata": (
            _pydantic_dump(payload.generated_output_metadata)
            if payload.generated_output_metadata is not None
            else None
        ),
        "auto_score": auto_score,
    }
    _topic2_submissions.append(submission)
    _topic2_score_counts_by_nickname[nick_key] += 1

    leaderboard_rows = _build_topic2_leaderboard_rows()
    return {
        "ok": True,
        "submission_id": submission_id,
        "timestamp_utc": submission["submitted_at_utc"],
        "auto_score": auto_score,
        "google_sheets_export_preview": _google_sheets_export_preview(submission),
        "leaderboard_snapshot": {
            "top": leaderboard_rows[:5],
            "bottom": leaderboard_rows[-5:] if len(leaderboard_rows) > 5 else leaderboard_rows,
        },
    }


def _build_topic2_leaderboard_rows() -> list[dict[str, Any]]:
    rows = []
    for sub in _topic2_submissions:
        avg = sub.get("auto_score", {}).get("average_score")
        if avg is None:
            continue
        rows.append(
            {
                "submission_id": sub.get("submission_id"),
                "nickname": sub.get("nickname"),
                "average_score": avg,
                "submitted_at_utc": sub.get("submitted_at_utc"),
                "publish_to_community": sub.get("publish_to_community", False),
                "audio_url": (sub.get("generated_output_metadata") or {}).get("audio_url"),
            }
        )
    rows.sort(key=lambda r: (-float(r["average_score"]), str(r["submitted_at_utc"])))
    return rows


@app.get("/topic2/leaderboard")
async def topic2_leaderboard(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    rows = _build_topic2_leaderboard_rows()
    return {
        "ok": True,
        "count": len(rows),
        "top": rows[:10],
        "bottom": rows[-10:] if len(rows) > 10 else rows,
    }


@app.get("/topic2/cohort-summary")
async def topic2_cohort_summary(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    return {
        "ok": True,
        "generated_at_utc": _utc_now_iso(),
        "cohort_analytics": _cohort_analytics(),
    }


@app.get("/topic2/community-songs")
async def topic2_community_songs(
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    rows = []
    for sub in _build_topic2_leaderboard_rows():
        if not sub.get("publish_to_community"):
            continue
        rows.append(
            {
                **sub,
                "votes": len(_topic2_votes_by_submission.get(str(sub["submission_id"]), set())),
            }
        )
    rows.sort(key=lambda r: (-int(r["votes"]), -float(r["average_score"])))
    return {"ok": True, "songs": rows}


@app.post("/topic2/vote")
async def topic2_vote(
    payload: Topic2VoteRequest,
    request: Request,
    x_proxy_token: str | None = Header(default=None, alias="X-Proxy-Token"),
):
    _enforce_rate_limit(request)
    _require_token_if_enabled(x_proxy_token)
    target = next((s for s in _topic2_submissions if s.get("submission_id") == payload.submission_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if not target.get("publish_to_community"):
        raise HTTPException(status_code=400, detail="Submission is not published to the community list.")

    voter_key = _nickname_key(payload.voter_nickname)
    if not voter_key:
        raise HTTPException(status_code=400, detail="Voter nickname is required.")
    if voter_key == _nickname_key(str(target.get("nickname", ""))):
        raise HTTPException(status_code=400, detail="You cannot vote for your own submission.")

    _topic2_votes_by_submission[payload.submission_id].add(voter_key)
    return {
        "ok": True,
        "submission_id": payload.submission_id,
        "votes": len(_topic2_votes_by_submission[payload.submission_id]),
    }
