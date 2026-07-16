"""
Reusable tutorial builder for interactive tutorials (e.g. Monetary Economics EC3014).

ONE Streamlit app serves every topic. A tutorial is just a JSON file in
./tutorials/ -- drop in a new file and it appears automatically. No code
changes are needed to add a topic, so teachers/colleagues can create any number
of tutorials WITHOUT coding. This replaces the need for a separate
topicXquestions.qmd / Hugging Face Space per topic.

Two clearly separated views (chosen in the sidebar):
  * Teacher mode  -- build/edit a tutorial and save it as JSON (optionally
                     persisted to a Hugging Face Dataset so it survives restarts).
  * Student mode  -- work through a tutorial, get AI feedback, export answers.

Tutorial JSON schema:
{
  "topic_number": "2",
  "topic_name":   "Classical Theory of Money",
  "title":        "Topic 2 Questions",
  "intro":        "markdown shown above the questions",
  "readings":     "markdown list of readings",
  "questions": [
    {"title": "...", "prompt": "markdown + $LaTeX$", "suggested_answer": "markdown"}
  ]
}

Optional environment variables (set as Hugging Face Space secrets):
  GROQ_API_KEY[, GROQ_API_KEY_FALLBACK_1, GROQ_API_KEY_FALLBACK_2]  -> enables AI feedback
  HF_TOKEN                                                          -> enables persistence
  HF_DATASET_REPO  (e.g. "your-username/ec3014-tutorials")          -> where tutorials persist
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TUTORIALS_DIR = Path(__file__).parent / "tutorials"
TUTORIALS_DIR.mkdir(exist_ok=True)
REPO_ROOT = Path(__file__).resolve().parents[2]

FEEDBACK_MODEL = "llama-3.3-70b-versatile"

DEFAULT_INTRO = """Use this page to practise **concept clarity** and **economic reasoning** before your tutorial.

**How to use the AI tutor:**
1. Write your own answer first.
2. Use **Get AI feedback** for hints, not final answers.
3. Revise your reasoning before you reveal the indicative answer.
4. Bring remaining uncertainties to your human tutor, who remains the primary academic feedback source.

⚠️ **Important:** AI models can hallucinate or produce plausible-sounding but incorrect explanations. Verify claims against your notes and readings.
"""


# --------------------------------------------------------------------------- #
# Persistence: local folder + optional Hugging Face Dataset
# --------------------------------------------------------------------------- #
def _hf_config() -> tuple[str, str] | None:
    """Return (token, repo_id) if HF persistence is configured, else None."""
    token = os.environ.get("HF_TOKEN", "").strip()
    repo = os.environ.get("HF_DATASET_REPO", "").strip()
    return (token, repo) if token and repo else None


@st.cache_resource(show_spinner=False)
def sync_from_hub() -> str:
    """Pull any tutorials stored in the configured HF Dataset into the local
    folder. Cached so it runs once per server start. Safe no-op if unconfigured."""
    cfg = _hf_config()
    if cfg is None:
        return "local-only"
    token, repo = cfg
    try:
        from huggingface_hub import HfApi, hf_hub_download

        api = HfApi(token=token)
        files = api.list_repo_files(repo_id=repo, repo_type="dataset")
        for fname in files:
            if fname.endswith(".json"):
                src = hf_hub_download(
                    repo_id=repo, filename=fname, repo_type="dataset", token=token
                )
                (TUTORIALS_DIR / Path(fname).name).write_bytes(Path(src).read_bytes())
        return "synced"
    except Exception as exc:  # noqa: BLE001 - surface, never crash the app
        return f"sync-error: {exc}"


def push_to_hub(path: Path) -> str:
    """Upload one tutorial JSON to the HF Dataset. Returns a status message."""
    cfg = _hf_config()
    if cfg is None:
        return "Persistence not configured (set HF_TOKEN and HF_DATASET_REPO secrets)."
    token, repo = cfg
    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        api.create_repo(repo_id=repo, repo_type="dataset", exist_ok=True)
        api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo=path.name,
            repo_id=repo,
            repo_type="dataset",
            commit_message=f"Add/update tutorial {path.name}",
        )
        return f"Persisted to Hugging Face Dataset `{repo}`."
    except Exception as exc:  # noqa: BLE001
        return f"Could not persist to Hub: {exc}"


# --------------------------------------------------------------------------- #
# Data access
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).strip().lower()).strip("-")
    return slug or "tutorial"


def strip_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2].lstrip("\r\n") if len(parts) == 3 else text


def strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def clean_markdown_block(text: str) -> str:
    text = strip_code_fences(text)
    text = re.sub(r"^:::.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^<iframe.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```\{=html\}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^###\s+Indicative Answer.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+Questions.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+Topic\s+\d+\s+-\s+Questions.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+Interactive Tutorial with AI Feedback.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_question_sections(text: str) -> list[dict[str, str]]:
    text = strip_front_matter(text)
    if "## Questions" in text:
        text = text.split("## Questions", 1)[1]
    elif "## Questions on Topic" in text:
        text = text.split("## Questions on Topic", 1)[1]

    pattern = re.compile(r"^(#{2,3})\s+Question\s+(\d+)\s*:?\s*(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        raw_title = match.group(3).strip()
        title = raw_title or f"Question {match.group(2)}"
        body = clean_markdown_block(text[start:end])
        if not body:
            continue
        sections.append({
            "number": match.group(2),
            "title": title,
            "prompt": body,
        })
    return sections


def extract_answer_sections(text: str) -> dict[str, str]:
    text = strip_front_matter(text)
    pattern = re.compile(r"^##\s+Question\s+(\d+)\s*:?\s*(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    answers: dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        if "### Indicative Answer" in block:
            block = block.split("### Indicative Answer", 1)[1].strip()
        answers[match.group(1)] = clean_markdown_block(block)
    return answers


def extract_answer_blocks(text: str) -> dict[str, dict[str, str]]:
    text = strip_front_matter(text)
    pattern = re.compile(r"^##\s+Question\s+(\d+)\s*:?\s*(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    blocks: dict[str, dict[str, str]] = {}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        prompt = ""
        answer = block
        if "### Indicative Answer" in block:
            prompt, answer = block.split("### Indicative Answer", 1)
        blocks[match.group(1)] = {
            "title": (match.group(2).strip() or f"Question {match.group(1)}"),
            "prompt": clean_markdown_block(prompt),
            "answer": clean_markdown_block(answer),
        }
    return blocks


def extract_topic_name(topic_number: int, questions_text: str, reading_text: str, title: str) -> str:
    match = re.search(
        rf"^##\s+Questions\s+on\s+Topic\s+{topic_number}\s*[-:]\s*(.+)$",
        questions_text,
        flags=re.MULTILINE,
    )
    if match:
        return match.group(1).strip()

    if reading_text:
        reading_title = re.search(r'^title:\s*"([^"]+)"', reading_text, flags=re.MULTILINE)
        if reading_title:
            cleaned = re.sub(rf"^Topic\s+{topic_number}\s*[-:]\s*", "", reading_title.group(1)).strip()
            if cleaned and cleaned.lower() not in {f"topic {topic_number}", "monetary economics"}:
                return cleaned

        first_heading = re.search(r"^#\s+(.+)$", strip_front_matter(reading_text), flags=re.MULTILINE)
        if first_heading:
            return first_heading.group(1).strip()

    cleaned_title = re.sub(rf"^Topic\s+{topic_number}\s*[-:]?\s*", "", title).replace("Questions", "")
    cleaned_title = cleaned_title.strip(" -")
    return cleaned_title or f"Topic {topic_number}"


def extract_reading_summary(text: str) -> str:
    text = clean_markdown_block(strip_front_matter(text))
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    kept: list[str] = []
    headings_seen = 0
    for line in lines:
        if line.startswith("## "):
            headings_seen += 1
            if headings_seen > 1:
                break
        kept.append(line)
    return "\n".join(kept).strip()


def build_tutorial_from_qmd(topic_number: int) -> dict | None:
    questions_path = REPO_ROOT / f"topic{topic_number}questions.qmd"
    answers_path = REPO_ROOT / f"topic{topic_number}answers.qmd"
    reading_path = REPO_ROOT / f"topic{topic_number}reading.qmd"
    if not questions_path.exists() or not answers_path.exists():
        return None

    questions_text = questions_path.read_text(encoding="utf-8")
    question_sections = extract_question_sections(questions_text)
    answer_blocks = extract_answer_blocks(answers_path.read_text(encoding="utf-8"))
    if not question_sections:
        question_sections = [
            {
                "number": number,
                "title": block["title"],
                "prompt": block["prompt"],
            }
            for number, block in sorted(answer_blocks.items(), key=lambda item: int(item[0]))
            if block["prompt"]
        ]
    if not question_sections:
        return None

    answers_by_number = {number: block["answer"] for number, block in answer_blocks.items()}
    title_match = re.search(r'^title:\s*"([^"]+)"', questions_text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"Topic {topic_number} Questions"
    readings = ""
    reading_text = ""
    if reading_path.exists():
        reading_text = reading_path.read_text(encoding="utf-8")
        readings = extract_reading_summary(reading_text)
    topic_name = extract_topic_name(topic_number, questions_text, reading_text, title)

    questions = []
    for section in question_sections:
        questions.append(
            {
                "title": section["title"],
                "prompt": section["prompt"],
                "suggested_answer": answers_by_number.get(section["number"], ""),
            }
        )

    return {
        "topic_number": str(topic_number),
        "topic_name": topic_name or f"Topic {topic_number}",
        "title": title,
        "intro": DEFAULT_INTRO,
        "readings": readings,
        "questions": questions,
    }


def bootstrap_repo_tutorials() -> None:
    existing_topic_numbers: set[str] = set()
    for existing in TUTORIALS_DIR.glob("*.json"):
        try:
            data = json.loads(existing.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        topic_number = str(data.get("topic_number", "")).strip()
        if topic_number:
            existing_topic_numbers.add(topic_number)

    topic_paths = sorted(REPO_ROOT.glob("topic*questions.qmd"))
    for path in topic_paths:
        match = re.search(r"topic(\d+)questions\.qmd$", path.name)
        if not match:
            continue
        topic_number = int(match.group(1))
        if str(topic_number) in existing_topic_numbers:
            continue
        data = build_tutorial_from_qmd(topic_number)
        if data is None:
            continue
        destination_name = slugify(f"topic{data['topic_number']}-{data['topic_name']}")
        destination = TUTORIALS_DIR / f"{destination_name}.json"
        if destination.exists():
            continue
        destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        existing_topic_numbers.add(str(topic_number))


def resolve_query_tutorial(tutorials: dict[str, Path]) -> str | None:
    requested = str(st.query_params.get("tutorial", "")).strip().lower()
    if not requested:
        return None
    for label, path in tutorials.items():
        data = load_tutorial(path)
        candidates = {
            label.lower(),
            path.stem.lower(),
            slugify(label),
            slugify(data.get("title", "")),
            f"topic{data.get('topic_number', '')}".lower(),
        }
        if requested in candidates:
            return label
    return None


def list_tutorials() -> dict[str, Path]:
    bootstrap_repo_tutorials()
    out: dict[str, Path] = {}
    for path in sorted(TUTORIALS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            label = data.get("title") or path.stem
            num = data.get("topic_number")
            if num:
                label = f"Topic {num}: {data.get('topic_name', label)}"
        except (json.JSONDecodeError, OSError):
            label = f"{path.stem} (unreadable)"
        out[label] = path
    return out


def load_tutorial(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_tutorial(data: dict) -> Path:
    stem = slugify(f"topic{data.get('topic_number', '')}-{data.get('topic_name', data.get('title', ''))}")
    path = TUTORIALS_DIR / f"{stem}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# AI feedback (Groq) -- generalised across topics, hints not answers
# --------------------------------------------------------------------------- #
def get_groq_api_keys() -> list[str]:
    """Return configured Groq API keys in priority order (mirrors other Spaces)."""
    keys: list[str] = []
    for env_name in ["GROQ_API_KEY", "GROQ_API_KEY_FALLBACK_1", "GROQ_API_KEY_FALLBACK_2"]:
        value = os.environ.get(env_name, "").strip()
        if value and value not in keys:
            keys.append(value)
    return keys


def feedback_available() -> bool:
    return bool(get_groq_api_keys())


def build_feedback_prompt(tutorial: dict, question: dict, student_answer: str) -> str:
    topic = tutorial.get("topic_name") or tutorial.get("title", "this topic")
    return f"""You are an expert tutor giving feedback on a question from "{topic}".
Your goal is to help the student improve through HINTS and guidance, NOT to give
the complete answer.

QUESTION:
{question.get('prompt', '')}

STUDENT'S ANSWER:
{student_answer}

INDICATIVE ANSWER (for your reference only - DO NOT reproduce it directly):
{question.get('suggested_answer', '(none provided)')}

INSTRUCTIONS:
1. Acknowledge what the student got right.
2. Where the answer is incomplete or wrong, give hints that nudge toward the
   correct reasoning (definitions, setup, the missing causal step) without
   handing over the solution.
3. For multi-part questions, address each part briefly.
4. Encourage economic intuition, not just mechanics.
5. Keep it concise (200-250 words), encouraging and constructive.

Provide your feedback now:"""


def get_ai_feedback(tutorial: dict, question: dict, student_answer: str) -> str:
    if not student_answer.strip():
        return "Please write an answer first, then request feedback."
    api_keys = get_groq_api_keys()
    if not api_keys:
        return "AI feedback is not enabled for this Space (no GROQ_API_KEY set)."
    try:
        from groq import Groq
    except ImportError:
        return "The `groq` package is not installed. Add it to requirements.txt."

    prompt = build_feedback_prompt(tutorial, question, student_answer)
    last_err = ""
    for key in api_keys:  # rotate through keys on failure (e.g. rate limit)
        try:
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=FEEDBACK_MODEL,
            )
            return resp.choices[0].message.content
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            continue
    return f"Could not get feedback (all keys failed). Last error: {last_err}"


# --------------------------------------------------------------------------- #
# Teacher mode
# --------------------------------------------------------------------------- #
def teacher_view() -> None:
    st.header("👩‍🏫 Teacher mode — build a tutorial")
    st.caption(
        "Fill in the fields (or load an existing tutorial to edit), then **Save**. "
        "Math uses LaTeX: `$x$` inline, `$$x$$` for display. No coding required."
    )

    seed: dict = {}
    existing = list_tutorials()
    with st.expander("Start from an existing tutorial (optional)"):
        col_a, col_b = st.columns(2)
        with col_a:
            pick = st.selectbox("Load saved tutorial", ["— none —", *existing.keys()])
            if pick != "— none —" and st.button("Load for editing"):
                st.session_state["teacher_seed"] = load_tutorial(existing[pick])
        with col_b:
            up = st.file_uploader("…or upload a tutorial JSON", type="json")
            if up is not None:
                st.session_state["teacher_seed"] = json.loads(up.read().decode("utf-8"))

    seed = st.session_state.get("teacher_seed", {})

    col1, col2 = st.columns(2)
    topic_number = col1.text_input("Topic number", value=seed.get("topic_number", ""))
    topic_name = col2.text_input("Topic name", value=seed.get("topic_name", ""))
    title = st.text_input(
        "Tutorial title",
        value=seed.get("title", f"Topic {topic_number} Questions" if topic_number else ""),
    )
    intro = st.text_area("Intro / instructions (markdown)", value=seed.get("intro", ""), height=120)
    readings = st.text_area(
        "Readings (markdown — paste a list, or upload below)",
        value=seed.get("readings", ""),
        height=140,
    )
    up_readings = st.file_uploader("…or upload readings (.md/.txt)", type=["md", "txt"], key="rd")
    if up_readings is not None:
        readings = up_readings.read().decode("utf-8")

    st.subheader("Questions")
    seed_qs = seed.get("questions", [])
    n = st.number_input(
        "How many questions?", min_value=1, max_value=30, value=max(1, len(seed_qs)), step=1
    )

    questions = []
    for i in range(int(n)):
        sq = seed_qs[i] if i < len(seed_qs) else {}
        with st.expander(f"Question {i + 1}", expanded=i == 0):
            q_title = st.text_input("Short title", value=sq.get("title", ""), key=f"qt{i}")
            prompt = st.text_area(
                "Question (markdown + LaTeX)", value=sq.get("prompt", ""), height=160, key=f"qp{i}"
            )
            answer = st.text_area(
                "Suggested / indicative answer (markdown + LaTeX)",
                value=sq.get("suggested_answer", ""),
                height=160,
                key=f"qa{i}",
            )
        questions.append({"title": q_title, "prompt": prompt, "suggested_answer": answer})

    data = {
        "topic_number": topic_number.strip(),
        "topic_name": topic_name.strip(),
        "title": title.strip() or "Untitled tutorial",
        "intro": intro,
        "readings": readings,
        "questions": questions,
    }

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("💾 Save tutorial", type="primary"):
        path = save_tutorial(data)
        st.success(f"Saved locally → `{path.name}`")
        st.info(push_to_hub(path))
        st.cache_resource.clear()  # so Student mode sees the new/updated file
    c2.download_button(
        "⬇️ Download JSON",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=f"{slugify('topic' + topic_number + '-' + topic_name)}.json",
        mime="application/json",
    )

    with st.expander("Preview the JSON that will be saved"):
        st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")


# --------------------------------------------------------------------------- #
# Student mode
# --------------------------------------------------------------------------- #
def student_view() -> None:
    tutorials = list_tutorials()
    if not tutorials:
        st.info("No tutorials yet. Switch to **Teacher mode** to create one.")
        return

    labels = list(tutorials.keys())
    query_label = resolve_query_tutorial(tutorials)
    default_index = labels.index(query_label) if query_label in labels else 0
    label = st.sidebar.selectbox("Choose a tutorial", labels, index=default_index)
    data = load_tutorial(tutorials[label])

    st.title(data.get("title", "Tutorial"))
    if data.get("topic_name"):
        st.caption(f"Topic {data.get('topic_number', '')} — {data['topic_name']}")
    if data.get("intro"):
        st.markdown(data["intro"])
    if data.get("readings"):
        with st.expander("📚 Readings", expanded=True):
            st.markdown(data["readings"])

    ai_on = feedback_available()
    if not ai_on:
        st.sidebar.caption("ℹ️ AI feedback disabled (no GROQ_API_KEY set).")
    st.divider()

    answers: dict[str, str] = {}
    for i, q in enumerate(data.get("questions", []), start=1):
        heading = f"Question {i}" + (f": {q['title']}" if q.get("title") else "")
        st.subheader(heading)
        st.markdown(q.get("prompt", ""))

        ans = st.text_area(
            "Your answer",
            key=f"student_ans_{i}",
            height=180,
            placeholder="Write your own answer first, before revealing the suggested answer…",
        )
        answers[heading] = ans

        fb_key = f"feedback_{i}"
        if ai_on and st.button("🤖 Get AI feedback", key=f"fb_btn_{i}"):
            with st.spinner("Asking the AI tutor…"):
                st.session_state[fb_key] = get_ai_feedback(data, q, ans)
        if st.session_state.get(fb_key):
            st.info(st.session_state[fb_key])
            st.caption(
                "⚠️ AI can be wrong or hallucinate. Verify against lecture notes and "
                "bring your answer to your tutor — the tutor is your primary feedback source."
            )

        with st.expander("💡 Reveal suggested answer"):
            st.markdown(q.get("suggested_answer", "_No suggested answer provided._"))
        st.divider()

    # Export student responses (and any AI feedback received) as markdown.
    st.sidebar.divider()
    st.sidebar.subheader("Export your answers")
    lines = [f"# {data.get('title', 'Tutorial')}", ""]
    for i, (heading, ans) in enumerate(answers.items(), start=1):
        lines += [f"## {heading}", "", ans or "_(no answer)_", ""]
        fb = st.session_state.get(f"feedback_{i}")
        if fb:
            lines += ["**AI feedback:**", "", fb, ""]
    md = "\n".join(lines)
    st.sidebar.download_button(
        "⬇️ Download my answers (.md)",
        data=md,
        file_name=f"{slugify(data.get('title', 'answers'))}-responses-{datetime.now():%Y%m%d}.md",
        mime="text/markdown",
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(page_title="Tutorial Builder", page_icon="📘", layout="centered")
    sync_from_hub()  # pull persisted tutorials once per server start (no-op if unconfigured)
    mode = st.sidebar.radio("Mode", ["Student", "Teacher"], index=0)
    st.sidebar.divider()
    if mode == "Teacher":
        teacher_view()
    else:
        student_view()


if __name__ == "__main__":
    main()
