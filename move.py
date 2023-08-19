from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile

filepath_json = f'/Users/radioproducer/Documents/verslibre-mixcloud/credentials.json'

def login_with_service_account():
    """
    Google Drive service with a service account.
    note: for the service account to work, you need to share the folder or
    files with the service account email.

    :return: google auth
    """
    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    settings = {
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": filepath_json,
                }
            }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth

def copy(drive, file_id, new_title,target_folder_id):
    file = drive.CreateFile({'id': file_id})
    target_folder={}
    target_folder["id"]=target_folder_id
    file.Copy(target_folder=target_folder,new_title =new_title)

def move(file_id, new_parent):
    files = drive.auth.service.files()
    file  = files.get(fileId= file_id, fields= 'parents').execute()
    prev_parents = ','.join(p['id'] for p in file.get('parents'))
    file  = files.update( fileId = file_id,
                          addParents = new_parent,
                          removeParents = prev_parents,
                          fields = 'id, parents',
                          supportsAllDrives=True,
                          supportsTeamDrives=True
                          ).execute()

def download(file_id, file_name):
    trim_file_name=file_name.split('.',2)[0]
    file_name_new = f"{trim_file_name}.mp3"
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(f"/Users/radioproducer/Documents/verslibre-mixcloud/tmp/{file_name_new}", chunksize=1004857600)

drive = GoogleDrive(login_with_service_account()) # Create GoogleDrive instance with authenticated GoogleAuth instance

folderid_auphonic_macmini="1ZbwEJnbv6OXJ3PF4cwMurElgHpZHClK7"
folderid_auphonic="1jX5SgOub7DKdyPUznNEGmEf0krf4fVyH"
folderid_auphonic_preprocess="12Wn1XiyCDTAn1xI14CXuDTvT4aYl6DWr"
folderid_upload="1wGLWtfs4qEhHH_wtD2FPnEhp-n0s3haY"
folderid_upload_source="1My8d_fthYsRg0yV59kkkTtX6pktxFWu8"
folderid_sent="1tLBobAXugrZ5cHTP6X4Zk0LJDYnoZsN5"

# Auphonic on Macmini to auphonic upload
file_list_auphonic = drive.ListFile({'q': f"parents = '{folderid_auphonic_macmini}'"}).GetList()
for file in file_list_auphonic:
      id = file['id']
      title = file['title']
      file = drive.CreateFile({'id': file['id']})
      copy(drive, id, title,folderid_auphonic_preprocess)
      move(id,folderid_sent)

# Download from Auphonic upload
file_list_auphonic_new = drive.ListFile({'q': f"parents = '{folderid_auphonic}'"}).GetList()
for file in file_list_auphonic_new:
      id = file['id']
      title = file['title']
      file = drive.CreateFile({'id': file['id']})
      download(id,title)
      move(id,folderid_sent)

# Download from upload
file_list_upload = drive.ListFile({'q': f"parents = '{folderid_upload_source}'"}).GetList()
for file in file_list_upload:
      id = file['id']
      title = file['title']
      file = drive.CreateFile({'id': file['id']})
      download(id,title)
      move(id,folderid_sent)
