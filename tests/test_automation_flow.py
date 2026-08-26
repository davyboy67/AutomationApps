import asyncio
import contextlib
import os

import pytest

os.environ.setdefault("EKU_USER", "test-user")
os.environ.setdefault("EKU_PASS", "test-pass")

import main
from apintegrations import gdrive


@contextlib.asynccontextmanager
async def fake_playwright():
    yield None


class Harness:
    def __init__(self):
        self.logs = []
        self.emails = []
        self.launched = False


@pytest.fixture
def harness(monkeypatch):
    h = Harness()

    async def fake_email(year_month):
        h.emails.append(year_month)
        return True

    monkeypatch.setattr(main, "async_playwright", fake_playwright)
    monkeypatch.setattr(main, "send_final_attempt_failure_email", fake_email)
    monkeypatch.setattr(main, "log_to_db", lambda rid, pn, ok, msg: h.logs.append((ok, msg)))
    return h


def configure(monkeypatch, harness, *, downloaded, already_retrieved, final_attempt):
    async def fake_run(playwright):
        harness.launched = True
        return downloaded

    monkeypatch.setattr(main, "run", fake_run)
    monkeypatch.setattr(main, "bill_already_retrieved", lambda pn: already_retrieved)
    monkeypatch.setenv("FINAL_ATTEMPT", "true" if final_attempt else "false")


def test_bill_published_logs_success(monkeypatch, harness):
    configure(monkeypatch, harness, downloaded=True, already_retrieved=False, final_attempt=False)

    asyncio.run(main.main())

    assert harness.logs == [(True, "Successfully completed.")]
    assert harness.emails == []


def test_bill_missing_logs_and_exits_green(monkeypatch, harness):
    configure(monkeypatch, harness, downloaded=False, already_retrieved=False, final_attempt=False)

    asyncio.run(main.main())

    successful, message = harness.logs[0]
    assert successful is False
    assert "not yet published" in message
    assert harness.emails == []


def test_final_attempt_still_missing_emails_and_fails(monkeypatch, harness):
    configure(monkeypatch, harness, downloaded=False, already_retrieved=False, final_attempt=True)

    with pytest.raises(SystemExit) as exit_info:
        asyncio.run(main.main())

    assert exit_info.value.code == 1
    successful, message = harness.logs[0]
    assert successful is False
    assert "final attempt" in message
    assert len(harness.emails) == 1


def test_already_retrieved_skips_before_launching_browser(monkeypatch, harness):
    configure(monkeypatch, harness, downloaded=True, already_retrieved=True, final_attempt=True)

    asyncio.run(main.main())

    assert harness.launched is False
    assert harness.emails == []
    assert harness.logs[0][0] is True
    assert "Skipped" in harness.logs[0][1]


def test_manual_dispatch_after_success_does_not_resend(monkeypatch, harness):
    """FINAL_ATTEMPT is empty on workflow_dispatch; the guard must still apply."""
    configure(monkeypatch, harness, downloaded=True, already_retrieved=True, final_attempt=False)
    monkeypatch.delenv("FINAL_ATTEMPT", raising=False)

    asyncio.run(main.main())

    assert harness.launched is False
    assert "Skipped" in harness.logs[0][1]


def test_run_failure_is_logged_and_reraised(monkeypatch, harness):
    async def failing_run(playwright):
        raise RuntimeError("Failed to send the statement via email.")

    monkeypatch.setattr(main, "run", failing_run)
    monkeypatch.setattr(main, "bill_already_retrieved", lambda pn: False)
    monkeypatch.setenv("FINAL_ATTEMPT", "false")

    with pytest.raises(RuntimeError):
        asyncio.run(main.main())

    successful, message = harness.logs[0]
    assert successful is False
    assert "Failed with error" in message


class FakeFiles:
    def __init__(self, existing, calls):
        self.existing = existing
        self.calls = calls

    def list(self, **kwargs):
        self.calls.append("list")
        return FakeRequest({"files": self.existing})

    def create(self, **kwargs):
        self.calls.append("create")
        return FakeRequest({"id": "created-id"})


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


@pytest.fixture
def drive(monkeypatch, tmp_path):
    for key in ("GDRIVE_CLIENT_ID", "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN", "GDRIVE_FOLDER_ID"):
        monkeypatch.setenv(key, f"stub-{key}")
    monkeypatch.setattr(gdrive, "Credentials", lambda *a, **k: None)
    pdf = tmp_path / "EkurhuleniStatement-2026-08.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    return pdf


def test_upload_creates_file_when_folder_is_empty(monkeypatch, drive):
    calls = []
    monkeypatch.setattr(gdrive, "build", lambda *a, **k: type("S", (), {"files": lambda self: FakeFiles([], calls)})())

    gdrive.upload_to_drive(drive)

    assert calls == ["list", "create"]


def test_upload_rejects_duplicate_without_creating(monkeypatch, drive):
    calls = []
    monkeypatch.setattr(
        gdrive, "build",
        lambda *a, **k: type("S", (), {"files": lambda self: FakeFiles([{"id": "existing"}], calls)})(),
    )

    with pytest.raises(RuntimeError, match="already exists"):
        gdrive.upload_to_drive(drive)

    assert "create" not in calls


def test_upload_requires_credentials(monkeypatch, drive):
    monkeypatch.delenv("GDRIVE_FOLDER_ID", raising=False)
    monkeypatch.setattr(gdrive, "get_secret", lambda key, default=None: os.getenv(key))

    with pytest.raises(RuntimeError, match="not set"):
        gdrive.upload_to_drive(drive)
