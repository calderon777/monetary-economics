# Monetary Economics EC3014 site

Quarto website for course materials and quizzes. Builds to `docs/` for GitHub Pages.

## Structure
- `_quarto.yml`: site config, navbar, build output dir.
- `index.qmd`, `about.qmd`: landing and about pages.
- `week1_quiz.qmd`: self-check quiz (no persistence).
- `week1_quiz_leaderboard.qmd`: quiz with client-side scoring and optional leaderboard.
- `styles.css`: shared styling.

## Building locally
- Install Quarto and R with the `webexercises` package.
- Render the site: `quarto render` (outputs to `docs/`).

## Leaderboard and Google Apps Script
The leaderboard uses a Google Apps Script web app (POST/GET JSON). Replace the `ENDPOINT` value near the top of `week1_quiz_leaderboard.qmd` with your deployed URL.

### Quick setup
1) Create a new Google Sheet and note its ID.
2) In the sheet, add headers: `timestamp`, `nickname`, `quiz`, `score`, `total`, `details`.
3) Open Extensions -> Apps Script, replace the default script with:
```javascript
const SHEET_ID = 'PUT_YOUR_SHEET_ID_HERE';
const SHEET_NAME = 'Sheet1';

function doPost(e) {
  const body = JSON.parse(e.postData.contents || '{}');
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
  sheet.appendRow([
    body.timestamp || new Date().toISOString(),
    body.nickname || '',
    body.quiz || '',
    body.score || 0,
    body.total || 0,
    JSON.stringify(body.details || {})
  ]);
  return ContentService.createTextOutput('ok');
}

function doGet() {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
  const [header, ...rows] = sheet.getDataRange().getValues();
  const objRows = rows.map(r => ({
    timestamp: r[0], nickname: r[1], quiz: r[2], score: r[3], total: r[4], details: r[5]
  }));
  return ContentService.createTextOutput(JSON.stringify(objRows))
    .setMimeType(ContentService.MimeType.JSON);
}
```
4) Deploy -> New deployment -> type Web app; execute as "Me"; allow Anyone with the link.
5) Copy the web app URL and paste it into `ENDPOINT` in `week1_quiz_leaderboard.qmd`.

### Privacy note
Only nicknames and quiz scores are sent. If you need stricter privacy, avoid collecting names or IDs and keep the sheet access limited.

## Housekeeping
- `_site/` is an older build artifact; `docs/` is the publish target. Delete `_site/` if not needed.
