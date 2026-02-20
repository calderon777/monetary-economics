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

## Environment Variables

- `GROQ_API_KEY`: required. Set this as a Hugging Face Space secret.

## Model

- **API**: Groq
- **Model**: `llama-3.3-70b-versatile`

## Run Locally

```bash
pip install -r requirements.txt
shiny run app.py
```
