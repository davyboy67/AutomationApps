from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config.secrets import get_secret

TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/drive.file"


def upload_to_drive(file_path: Path) -> None:
    folder_id = get_secret("GDRIVE_FOLDER_ID")
    client_id = get_secret("GDRIVE_CLIENT_ID")
    client_secret = get_secret("GDRIVE_CLIENT_SECRET")
    refresh_token = get_secret("GDRIVE_REFRESH_TOKEN")

    if not folder_id or not client_id or not client_secret or not refresh_token:
        raise RuntimeError("Google Drive folder id or OAuth credentials not set.")

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
    )
    service = build("drive", "v3", credentials=credentials)

    filename = file_path.name
    # The token refresh happens lazily on this first request, so an expired or revoked
    # GDRIVE_REFRESH_TOKEN surfaces here rather than at Credentials().
    print(f"Google Drive: checking folder {folder_id} for an existing {filename}...")
    existing = service.files().list(
        q=f"name = '{filename}' and '{folder_id}' in parents and trashed = false",
        fields="files(id)",
    ).execute()
    if existing["files"]:
        raise RuntimeError(
            f"'{filename}' already exists in the Google Drive folder "
            f"(file id {existing['files'][0]['id']})."
        )

    print(f"Google Drive: uploading {filename} ({file_path.stat().st_size:,} bytes)...")
    created = service.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=MediaFileUpload(str(file_path), mimetype="application/pdf"),
        fields="id",
    ).execute()
    print(f"Google Drive: upload complete (file id {created['id']}).")
