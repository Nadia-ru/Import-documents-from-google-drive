from __future__ import print_function

import io
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from pip._vendor import chardet

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.document' or mimeType='application/msword' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
        file_id = input('Enter the ID of the file to download: ')

        # Get the file name and create a MediaIoBaseDownload object
        file = service.files().get(fileId=file_id).execute()
        name = file.get('name')
        base_name, _ = os.path.splitext(name)


        if str(file.get('mimeType')) == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=file_id,
                                                   mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            file_name = base_name + '.docx'
        else:
            request = service.files().get_media(fileId=file_id)
            file_name = base_name


        fh = io.BytesIO()


        downloader = MediaIoBaseDownload(fd=fh, request=request)

        # Download the file from Google Drive
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")
        fh.seek(0)

        if str(file.get('mimeType')) == 'application/vnd.google-apps.document':
            with open(os.path.join('./download', file_name), 'wb') as f:
                f.write(fh.read())
                f.close()


        print(f"File '{file_name}' has been downloaded from Google Drive.")
    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
