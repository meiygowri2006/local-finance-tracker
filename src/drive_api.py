import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

def download_latest_backup(destination_path="data/raw/sms_backup.xml"):
    print("[0/3] Fetching latest backup from Google Drive...")
    try:
        # 1. Wake up the bot
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials/service_account.json', scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # 2. Search for the newest XML file the bot has access to
        results = service.files().list(
            q="mimeType='text/xml' or name contains '.xml'",
            orderBy="createdTime desc",
            pageSize=1,
            fields="files(id, name)"
        ).execute()

        items = results.get('files', [])

        if not items:
            print("      -> ❌ No backups found. Did you share the Drive folder with the bot?")
            return False

        file_id = items[0]['id']
        file_name = items[0]['name']
        print(f"      -> Found newest backup: {file_name}")

        # 3. Download the file directly into your data/raw/ folder
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        print("      -> ✅ Download complete.")
        return True

    except Exception as e:
        print(f"      -> ❌ Google Drive Error: {e}")
        return False