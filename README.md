# Municipal Statement Automation

An unattended monthly job that collects the City of Ekurhuleni municipal statement from the
council's [Siyakhokha](https://siyakhokha.ekurhuleni.gov.za/) self-service portal, emails it on,
and files a copy in Google Drive — so nobody has to log in, find the right month, and forward a PDF
by hand.

The download itself is the easy part. Most of this project deals with what goes wrong around it:
the statement isn't always published on time, the portal changes its layout without notice, it is
slow and intermittently unreachable from cloud runners, and nobody is watching when the job runs.

## What it does

Each run, on a GitHub Actions schedule:

1. **Checks whether this month is already done.** It reads its own run log in Postgres; if this
   month's statement was already retrieved, it exits without touching the portal.
2. **Signs in to the portal** with a headless Chromium browser (Playwright) and opens the
   statements list.
3. **Checks the statement has actually been published.** If it hasn't, that's an expected outcome,
   not a fault: it's logged and the job exits cleanly, to try again later.
4. **Downloads the statement PDF**, **emails it** to a configured recipient as an attachment, and
   **uploads it to a Google Drive folder**, refusing to overwrite or duplicate a file of the same
   name.
5. **Records the outcome** — success, not yet published, or the error that stopped it — in an
   `AutomationAppLogs` table.

## Capabilities

- **Late-statement retry.** Runs on the 20th and again on the 25th. If the statement isn't out on
  the 20th, the 25th tries again; if it's still missing then, a final-attempt alert email is sent
  and the run fails visibly. See [Schedule](#schedule).
- **Idempotent.** The run log is the single source of truth for "already done this month", checked
  before any side effect — so a retry or a manual re-run never emails or files a statement twice.
- **Fails loudly, not silently.** A failed email or Drive upload fails the whole run rather than
  being reported as success, and is recorded with the underlying error. That keeps the month
  eligible for retry instead of marking it done.
- **Distinguishes "late" from "broken".** A statement that simply isn't published yet exits green;
  a real failure (portal down, credentials rejected, upload refused) exits red.
- **Tolerates a slow portal.** Longer timeouts, waiting on DOM readiness rather than full page
  load, and navigating past a page-loading overlay that otherwise blocks clicks.

## How it's built

| Piece | Role |
|---|---|
| [main.py](main.py) | Entry point: the already-done check, outcome branching, logging |
| [scripts/ekurhuleni.py](scripts/ekurhuleni.py) | Portal sign-in, publication check, download |
| [apintegrations/email.py](apintegrations/email.py) | Gmail SMTP delivery and the final-attempt alert |
| [apintegrations/gdrive.py](apintegrations/gdrive.py) | Google Drive upload with duplicate check |
| [postgres_connector.py](postgres_connector.py) | Writes and reads the `AutomationAppLogs` run log |
| [config/secrets.py](config/secrets.py) | Reads each setting from an env var (CI) or the OS keyring (local) |
| [automation_apps_e.yml](.github/workflows/automation_apps_e.yml) | Schedules the runs and injects secrets |

## Setup

Quick start (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install
pytest tests/test_automation_flow.py -q
```

Every setting is read from an environment variable first and the OS keyring second, so the same
code runs in GitHub Actions (repo secrets) and locally (keyring, service name
`Python Automation App`):

```powershell
python -m keyring set "Python Automation App" <KEY>
```

| Key | Purpose |
|---|---|
| `EKU_USER`, `EKU_PASS` | Siyakhokha portal login |
| `SENDER_EMAIL`, `SENDER_EMAIL_PASS` | Gmail account that sends the statement; the password is a Google **App Password**, not the account password |
| `TO_EMAIL` | Recipient of the statement and of failure alerts |
| `DB_CONN_STR` | Postgres connection string for `AutomationAppLogs` |
| `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN`, `GDRIVE_FOLDER_ID` | Google Drive upload — see below |

Run it locally with `python main.py`. To regenerate selectors after the portal changes, record a
session with `python -m playwright codegen https://siyakhokha.ekurhuleni.gov.za/` and port the
locators into `scripts/ekurhuleni.py` — the generated script runs headed, so keep
`expect_download` rather than its `expect_popup` for the headless CI run.

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
