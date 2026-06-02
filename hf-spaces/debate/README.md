---
title: AI Persona Debate
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---

# AI Persona Debate

Two-team debate app for EC3014. Students enter a topic and question, and two AI teams respond:
- **Classicals** (Walras + Marshall)
- **Keynesians** (Keynes + Hicks)

## Features

- Two-pane live debate interface
- Three rounds: Neutrality, Liquidity Preference, Policy at Low Rates
- Powered by Groq + Llama 3.3 70B
- CSV logging of Groq requests (including prompts and token usage)

## Environment Variables

- `GROQ_API_KEY`: required. Set this as a Hugging Face Space secret.
- `USAGE_LOG_CSV`: optional. Path for usage log CSV (default: `usage_logs.csv`).
- `DEBATE_SESSION_ID`: optional. Override session id written into CSV logs.

## Model

- **API**: Groq
- **Model**: `llama-3.3-70b-versatile`

## Run Locally

```bash
pip install -r requirements.txt
shiny run app.py
```

## Usage Exports

The app appends one row per Groq request to `usage_logs.csv` (or `USAGE_LOG_CSV` if set).
Each row includes:

- Timestamp/session metadata
- Debate context (topic, round, team, stage)
- Status/error
- Token usage (`prompt_tokens`, `completion_tokens`, `total_tokens`)
- `user_prompt`

Generate downloadable report files with:

```bash
python export_usage_reports.py --input usage_logs.csv
```

This creates:

- `usage_summary.csv` (aggregated by date/topic/round/team/stage/model)
- `user_prompts.csv` (prompt-only extract)
