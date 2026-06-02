---
title: Tutorial Builder
emoji: 📘
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Tutorial Builder (reusable across topics)

One Streamlit app that turns teacher-provided material into an interactive
student tutorial. It replaces the need for a separate `topicXquestions.qmd`
file or a separate Hugging Face Space per topic: every tutorial is just a JSON
file in [`tutorials/`](tutorials/), and the app discovers them automatically.

**Adding a new topic requires no code changes** — save a new JSON file (from
Teacher mode, or by hand) and it shows up in Student mode.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pick **Student** or **Teacher** in the sidebar.

## Modes

- **Teacher mode** — set the title, topic number/name, paste or upload
  readings, and add questions with suggested answers. Save to the
  `tutorials/` folder (and, if configured, to a Hugging Face Dataset so it
  survives restarts) or download the JSON. You can also load an existing
  tutorial (or upload a JSON) to edit it. No coding required.
- **Student mode** — choose a tutorial, read the intro and readings, answer
  each question, optionally **Get AI feedback** (hints, not answers), reveal
  the suggested answer to self-check, and download all your answers (with any
  AI feedback) as Markdown.

## Optional features (set as Hugging Face Space *Secrets*)

Both are optional — the app runs without them, just with those features off.

| Secret | Purpose |
| --- | --- |
| `GROQ_API_KEY` (plus optional `GROQ_API_KEY_FALLBACK_1/2`) | Enables the **Get AI feedback** button. Keys are tried in order if one is rate-limited. |
| `HF_TOKEN` (write-scoped) + `HF_DATASET_REPO` (e.g. `your-username/ec3014-tutorials`) | **Persistence.** Teacher saves are committed to that Dataset and pulled back on startup, so tutorials survive Space restarts. |

Without `HF_TOKEN`/`HF_DATASET_REPO`, saves are written to the local
`tutorials/` folder only (ephemeral on Spaces) — the **Download JSON** button
remains the durable fallback.

## Data format

One JSON file per tutorial in `tutorials/`. Schema:

```json
{
  "topic_number": "2",
  "topic_name": "Classical Theory of Money",
  "title": "Topic 2 Questions",
  "intro": "markdown shown above the questions",
  "readings": "markdown list of readings",
  "questions": [
    {
      "title": "Utility Maximization",
      "prompt": "markdown question text, with $LaTeX$ and $$display$$ math",
      "suggested_answer": "markdown indicative answer"
    }
  ]
}
```

LaTeX math is supported anywhere Markdown is rendered (`$inline$`, `$$display$$`).
See [`tutorials/topic3-keyness-theory-of-money.json`](tutorials/topic3-keyness-theory-of-money.json)
for a worked example (converted from `topic3questions.qmd`; the original `.qmd`
files in the repo are left untouched).

## Deploy

Deploy this single folder as one Hugging Face Space (Streamlit SDK). All topics
are served from it — no per-topic Space needed.
