import io
from datetime import datetime
from fastapi import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from app.auth import get_credentials


def get_drive_service(request: Request):
    """Get authenticated Google Drive service"""
    credentials = get_credentials(request)
    return build('drive', 'v3', credentials=credentials)


def read_file_from_drive(drive_service, file_id: str) -> str:
    """Read text file content from Google Drive"""
    try:
        # Get file content
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()

        # Decode bytes to string
        return file_content.decode('utf-8')

    except HttpError as error:
        raise Exception(f"Error reading file from Drive: {error}")


def save_to_drive(drive_service, filename: str, content: str, folder_id: str = None) -> str:
    """
    Save markdown content to Google Drive
    Returns the file URL
    folder_id: ID of folder to save to, or None for root
    """
    try:
        # Check if file already exists
        if folder_id:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        else:
            query = f"name='{filename}' and 'root' in parents and trashed=false"

        results = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()

        existing_files = results.get('files', [])

        # If file exists, rename with timestamp
        if existing_files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1] if '.' in filename else ''
            filename = f"{base_name}_{timestamp}.{extension}"

        # Create file metadata
        file_metadata = {
            'name': filename,
            'mimeType': 'text/markdown'
        }

        # Only add parents if folder_id is specified
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Create media content
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode('utf-8')),
            mimetype='text/markdown',
            resumable=True
        )

        # Upload file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('webViewLink', f"https://drive.google.com/file/d/{file.get('id')}/view")

    except HttpError as error:
        raise Exception(f"Error saving file to Drive: {error}")


def list_text_files(drive_service) -> list:
    """List all .txt files from user's Google Drive with folder paths"""
    try:
        query = "mimeType='text/plain' and trashed=false"
        results = drive_service.files().list(
            q=query,
            pageSize=1000,  # Increased to show more files
            fields="files(id, name, parents, modifiedTime)",
            orderBy="name"
        ).execute()

        files = results.get('files', [])

        # Get folder names for each file
        for file in files:
            if 'parents' in file and file['parents']:
                try:
                    # Get parent folder name
                    parent_id = file['parents'][0]
                    parent = drive_service.files().get(fileId=parent_id, fields="name").execute()
                    file['folderName'] = parent.get('name', 'Unknown')
                except:
                    file['folderName'] = 'Unknown'
            else:
                file['folderName'] = 'My Drive (Root)'

        return files

    except HttpError as error:
        raise Exception(f"Error listing files from Drive: {error}")
