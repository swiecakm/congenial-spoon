
#setup Google Drive API before usage
#https://developers.google.com/drive/api/v3/quickstart/python?hl=pl

#save credentials.json in the same directory as this script

from __future__ import print_function
import pickle
import os.path

from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import time


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

folderLink = 'https://drive.google.com/drive/folders/1vDYJ5qekijKwK69sfG0cdEN-suHRGhyO'

metadataDatetimeFormat = '%Y:%m:%d %H:%M:%S'
newImageNameFormat = '%Y%m%d%H%M%S'
dateFolderNameFormat = '%Y%m%d'

subfolderName = 'Sorted3'

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


def getImages(service, folderID, pageToken=None):
    '''
        folderID - You can find the folder ID entering it in web browser
    '''
    try:
        results = service.files().list(
            #to find other files metadata visit https://developers.google.com/drive/api/v3/reference/files
            fields="nextPageToken, files(id, name, imageMediaMetadata)", pageToken=pageToken,
            q="mimeType contains 'image/' and '{}' in parents and trashed=False".format(folderID)).execute()
    except errors.HttpError as err:
        if err.resp.status in [500, 503, 504]:
            print('Server error {}'.format(err.resp.status))
            print('Retrying getting files page in 5 seconds...'.format(image['name']))
            time.sleep(5)
            return getImages(service, folderID, pageToken=pageToken)
        else:
            print('Error during processing the file {}'.format(image['name']))
            raise

    return results.get('files', []), results.get('nextPageToken')


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


def getFolder(service, folderName, parentID):
    results = service.files().list(
        # to find other files metadata visit https://developers.google.com/drive/api/v3/reference/files
        fields="nextPageToken, files(id, name, imageMediaMetadata)",
        q="mimeType = 'application/vnd.google-apps.folder' and '{0}' in parents and name='{1}' and trashed=False".format(parentID,
                                                                                                       folderName)).\
        execute()

    if results['files']:
        return results['files'][0]
    else:
        return None


def createFolderOrGetExisting(service, folderName, parentID):
    folder = getFolder(service, folderName, parentID)
    if not folder:
        folder = createFolder(service, folderName, parentID)
    return folder


def processImage(service, sourceFolderID, newFolderID, image):
    if 'time' in image['imageMediaMetadata'].keys():
        print(u'{0} ({1}) {2}'.format(image['name'], image['id'], image['imageMediaMetadata']['time']))
        photoTakenDateTime = datetime.datetime.strptime(image['imageMediaMetadata']['time'], metadataDatetimeFormat)
        newFileName = '{0}{1}'.format(photoTakenDateTime.strftime(newImageNameFormat),
                                      os.path.splitext(image['name'])[1])
        dateFolderName = '{}'.format(photoTakenDateTime.strftime(dateFolderNameFormat))
        try:
            dateFolderID = createFolderOrGetExisting(service, dateFolderName, newFolderID)['id']

            metadata = {'name': newFileName}
            newFile = service.files().copy(fileId=image['id'], body=metadata).execute()
            service.files().update(fileId=newFile['id'], addParents=dateFolderID, removeParents=sourceFolderID).execute()

            # service.files().update(fileID=newFile['id'], addParents=dateFolderID).execute()
            print('created file {0} in {1} folder (from {2} file)'.format(newFileName, dateFolderName, image['name']))
        except errors.HttpError as err:
            if err.resp.status in [500, 503, 504]:
                print('Server error {}'.format(err.resp.status))
                print('Retrying processing the file {} in 5 seconds...'.format(image['name']))
                time.sleep(5)
                processImage(service, sourceFolderID, newFolderID, image)
            else:
                print('Error during processing the file {}'.format(image['name']))
                raise
    else:
        print('Cannot get the time for file {}'.format(image['name']))


if __name__ == '__main__':
    service = getService()
    rootParentID = os.path.split(folderLink)[-1]
    subparentID = createFolderOrGetExisting(service, subfolderName, rootParentID)['id']
    print('Subparent created {}'.format(subparentID))

    pageToken = None
    filesCount = 0

    while True:
        print("Retrieving page of files")
        images, pageToken = getImages(service, rootParentID, pageToken=pageToken)
        if not images:
            print('No files found.')
        else:
            for image in images:
                processImage(service, rootParentID, subparentID, image)
                filesCount += 1
                print('{} files processed'.format(filesCount))
        if not pageToken:
            break

