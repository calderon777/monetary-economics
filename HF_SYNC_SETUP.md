# HF Sync & AI Feedback Setup for Topic 1 Questions

## Overview

This document explains how the GitHub Actions workflow syncs `topic1questions` content to Hugging Face Space and integrates it with the AI feedback system in `app.py`.

---

## 1. GitHub Actions Workflow (`.github/workflows/hf-space-sync.yml`)

### What Changed

**Added Pre-Sync Quarto Render Step:**
```yaml
- name: Set up Quarto (for rendering topic1questions)
  uses: quarto-dev/quarto-actions/setup@v2
- name: Render topic1questions.qmd to HTML
  run: |
    quarto render topic1questions.qmd --to html
```

**Why?**
- **Ensures fresh HTML:** Every time you push to GitHub, the workflow automatically renders `topic1questions.qmd` → `docs/topic1questions.html`
- **No manual render needed:** You forget to render locally before pushing? No problem—GitHub does it for you
- **Syncs both source & rendered:** Both `topic1questions.qmd` (source) and `docs/topic1questions.html` (rendered) go to HF Space

**Files Synced to HF Space (Lean):**
- `app.py` — Shiny app (AI feedback engine)
- `shared.py` — Helper functions
- `requirements.txt` — Dependencies
- `Dockerfile` — Container config
- `README.hf.md` → `README.md` — Instructions
- `topic1questions.qmd` — Source file (for reference)
- `docs/topic1questions.html` — Rendered HTML (for viewing/context)

**Files NOT Synced (Large, stay on GitHub only):**
- `ppt/` folder (all PPTX + PNG)
- `docs/` images
- Anything else not explicitly copied

### How It Works

1. You push to `main` branch on GitHub
2. GitHub Actions triggers automatically
3. Workflow renders `topic1questions.qmd` → `docs/topic1questions.html`
4. Workflow copies lean files (app, config, topic1 content) to HF Space
5. HF Space updates with fresh content
6. AI feedback app on HF Space has access to question context

---

## 2. Integration in `app.py`

### What Changed

**Load Questions from QMD (Optional Context):**
```python
def load_questions_from_qmd():
    """Load question text from topic1questions.qmd for better context."""
    qmd_path = pathlib.Path("topic1questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            print(f"Warning: Could not load topic1questions.qmd: {e}")
    return None
```

**Enhanced Feedback Prompt:**
- The `create_feedback_prompt()` now calls `load_questions_from_qmd()`
- If `topic1questions.qmd` exists (on HF Space), the AI tutor has access to the full source for richer context
- Falls back gracefully if file is missing

**Updated UI:**
- Title: "Week 1 Tutorial Questions" → "Topic 1 - Monetary Economics Questions"
- Added links to `topic1questions.qmd` and `docs/topic1questions.html` in the instructions

### How It Benefits AI Feedback

1. **Context-Aware:** AI tutor can reference the original question file for more nuanced guidance
2. **Consistency:** Same questions on GitHub → HF Space → AI feedback system
3. **Decoupled:** Questions are not hardcoded in Python; they live in QMD files and are loaded dynamically

---

## 3. Pre-Sync Quarto Render Step Explained

### What It Does

A "pre-sync render" means: **before uploading to HF Space, render all QMD files to HTML locally (in GitHub Actions).**

```yaml
- name: Set up Quarto (for rendering topic1questions)
  uses: quarto-dev/quarto-actions/setup@v2
- name: Render topic1questions.qmd to HTML
  run: |
    quarto render topic1questions.qmd --to html
```

### Why You Need It

| Without Pre-Sync Render | With Pre-Sync Render |
|---|---|
| HF Space gets old/stale HTML | Fresh HTML synced every push |
| Manual render step easy to forget | Automatic, never forgotten |
| `docs/topic1questions.html` might be out of sync | Always up-to-date |

### Tradeoff

- **Time:** Adds ~30-60 seconds to workflow (rendering QMD → HTML)
- **Benefit:** Guaranteed fresh content on HF Space; no manual steps

### How to Scale It

To add more topics later (e.g., `topic2questions`, `topic3questions`):

```yaml
- name: Render all questions to HTML
  run: |
    quarto render topic1questions.qmd --to html
    quarto render topic2questions.qmd --to html
    quarto render topic3questions.qmd --to html
```

Then update the sync section to copy all rendered files:
```bash
cp docs/topic*.html "${WORKDIR}/docs/" 2>/dev/null || true
```

---

## 4. Workflow Summary

```
┌─────────────────────────────────────────┐
│ You push to GitHub (main branch)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ GitHub Actions Triggered                │
│ 1. Set up Quarto                        │
│ 2. Render topic1questions.qmd → HTML    │
│ 3. Copy lean files                      │
│ 4. Push to HF Space                     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ HF Space Updated                        │
│ - app.py ready to serve                 │
│ - topic1questions.qmd & HTML available  │
│ - AI feedback system has context        │
└─────────────────────────────────────────┘
```

---

## 5. Testing & Verification

After updating the workflow, test by:

1. **Push a small change to GitHub:**
   ```bash
   git add .
   git commit -m "Test HF sync workflow"
   git push origin main
   ```

2. **Check GitHub Actions:**
   - Go to your repo → "Actions" tab
   - Watch the "Sync HF Space" workflow run
   - Should complete in 1-2 minutes

3. **Verify on HF Space:**
   - Open your HF Space: `https://huggingface.co/spaces/camcalderon777/monetary-economics-questions`
   - Check that the app loads
   - Check files in the HF Space repo (should see `topic1questions.qmd`, `docs/topic1questions.html`)

---

## 6. Future Improvements

- Add `topic2questions`, `topic3questions`, etc. following the same pattern
- Render all `topicXquestions.qmd` files in a loop (don't repeat yourself)
- Consider adding a CI check: fail the workflow if Quarto render fails (to catch errors early)
- Optional: cache Quarto rendering to speed up workflow

---

## Files Modified

- `.github/workflows/hf-space-sync.yml` — Updated with pre-sync render + topic1 content sync
- `app.py` — Updated to load `topic1questions.qmd` dynamically and enhance feedback prompt
- `README.md` (this file) — Documentation

Done! The setup is now **lean, automatic, and scalable.**
