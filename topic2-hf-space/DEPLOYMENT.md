# Deployment Checklist for Topic 2 HF Space

## 1. Create New HuggingFace Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. **Name**: `monetary-economics-topic2-questions`
4. **License**: MIT
5. **SDK**: Docker (or Gradio if you prefer)
6. **Visibility**: Public

## 2. Upload Files

Upload these files to the space:
- [ ] `app.py`
- [ ] `requirements.txt`
- [ ] `README.md`
- [ ] `.env.example` (optional - for local testing)

## 3. Set Environment Variable

In your HuggingFace Space settings:
1. Go to Settings → Repository secrets
2. Add a new secret:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Your Groq API key from https://console.groq.com/keys

## 4. Test the Space

1. Wait for the space to build (usually 2-3 minutes)
2. Test both questions
3. Verify AI feedback is working
4. Check mobile responsiveness

## 5. Update topic2questions.qmd

Once your space is deployed at:
`https://huggingface.co/spaces/camcalderon777/monetary-economics-topic2-questions`

Update the iframe in topic2questions.qmd to:
```html
<iframe src="https://huggingface.co/spaces/camcalderon777/monetary-economics-topic2-questions/embed" frameborder="0" width="100%" height="1400"></iframe>
```

## 6. Deploy to Netlify

Run `quarto render` to rebuild your site with the new iframe link, then push to GitHub/deploy to Netlify.

## Notes

- The space name should match your HuggingFace username
- Make sure GROQ_API_KEY is set as a secret, not hardcoded
- Test thoroughly before updating topic2questions.qmd
