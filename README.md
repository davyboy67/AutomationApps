Playwright Python minimal scaffold

Quick start (PowerShell):

```powershell
cd c:\Users\david\Documents\Projects\Python\Automation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# install browsers
python -m playwright install
# run tests
pytest -q
# generate playwright script using codegen
python -m playwright codegen https://siyakhokha.ekurhuleni.gov.za// --target python --output scripts/animePahe.py
```

## Google Drive backup

Successful runs also upload the statement to a Drive folder. Set these locally via
`keyring set "Python Automation App" <KEY>` and as GitHub Actions secrets of the same name:

- `GDRIVE_CLIENT_ID` / `GDRIVE_CLIENT_SECRET` — from an OAuth 2.0 "Web application" client in
  Google Cloud, with the Drive API enabled and
  `https://developers.google.com/oauthplayground` registered as an authorised redirect URI.
- `GDRIVE_REFRESH_TOKEN` — minted once by hand against the
  `https://www.googleapis.com/auth/drive.file` scope.
- `GDRIVE_FOLDER_ID` — the trailing segment of the folder's URL
  (`https://drive.google.com/drive/folders/<this part>`).

Uploading a statement whose filename already exists in the folder is treated as a failure: nothing
is uploaded, the error is written to `AutomationAppLogs`, and the run exits non-zero.

### Publish the OAuth consent screen (do this before minting the refresh token)

Google Cloud Console → OAuth consent screen → Audience → **Publish app**, moving it out of
Testing. If it stays in Testing, `GDRIVE_REFRESH_TOKEN` silently stops working 7 days after it's
issued — it won't fail loudly until the next scheduled run, by which point it looks like an
unrelated outage.

Publish is blocked until the Branding page passes validation, even though most of its fields (home
page, privacy policy, terms of service) aren't marked required. If it won't clear:
- Fill **Developer contact information** (the one field that is required).
- If Authorised Domains flags a "Missing domain" error because one of those optional link fields
  points at a Google-hosted page (e.g. a Google Sites URL under `sites.google.com`), just add that
  domain (e.g. `google.com`) via **+ Add domain** and save. Google only checks real ownership via
  Search Console during full app verification review, which a low-usage app requesting a
  non-sensitive scope (`drive.file`) never triggers — self-declaring the domain is enough to clear
  this gate.

Redo the Playground exchange *after* publishing — a refresh token minted while still in Testing
doesn't retroactively gain the longer lifetime.

### If uploads start failing with `invalid_scope`

`google-auth` re-sends whatever `scopes` a `Credentials` object was constructed with on every token
refresh, and Google's refresh endpoint can reject that with `invalid_scope` even when it matches
the original grant — scope is already bound to the refresh token server-side and isn't meant to be
re-declared. [gdrive.py](apintegrations/gdrive.py) works around this by not passing `scopes=` to
`Credentials(...)`; if that argument reappears during a refactor, uploads will break with this
exact error.

## Schedule

The workflow runs on the 20th and again on the 25th. If the current month's bill has not been
published on the 20th, the run logs that and exits green without downloading. The 25th run skips
itself if the bill was already retrieved this month, otherwise it retries; if the bill is still
missing it emails a final-attempt failure notice and exits non-zero.

### How "this month's bill" is identified

The statements table shows a **due date**, not a bill date, and a statement issued in month M falls
due on the 5th of M+1 — the August 2026 statement is listed as `2026-09-05`. So the row is matched
on *next* month's `YYYY-MM`, not the current one. Matching on the current month silently selects
the previous month's statement, downloads it, and reports success. The downloaded file is still
named for the issue month (`EkurhuleniStatement-<current YYYY-MM>.pdf`), which is what the Drive
duplicate check and the `AutomationAppLogs` rows key off.
