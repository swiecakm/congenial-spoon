
#setup Google Drive API before usage
#https://developers.google.com/drive/api/v3/quickstart/python?hl=pl

#save credentials.json in the same directory as this script

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

folderLink = 'https://drive.google.com/drive/folders/1sdjRrR7QCks3kdHs-1S0LR3ou48hiK4c'

def getService():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def getImages(service, folderID):
    '''
        folderID - You can find the folder ID entering it in web browser
    '''

    results = service.files().list(
        #to find other files metadata visit https://developers.google.com/drive/api/v3/reference/files
        fields="nextPageToken, files(id, name, imageMediaMetadata)",
        q="mimeType contains 'image/' and '{}' in parents".format(folderID)).execute()

    return results.get('files', [])


def createFolder(service, folderName, parentID):
    file_metadata = {
        'name': folderName,
        'parents': [parentID],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata,
                                        fields='id').execute()
    print('Folder created {0}'.format(folder['id']))
    return folder


if __name__ == '__main__':
    service = getService()
    folderID = os.path.split(folderLink)[-1]
    images = getImages(service, folderID)
    if not images:
        print('No files found.')
    else:
        print('Files:')
        for image in images:
            print(u'{0} ({1}) {2}'.format(image['name'], image['id'], image['imageMediaMetadata']['time']))
    #folder = createFolder(service, 'JustTest', folderID)
