
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from pydub import AudioSegment
import os
from loguru import logger
from datetime import datetime

prerec_folder_id="181p00FNHEIsA6ozM_2iXhcBd9poeKBwOrD4KpgPW4MJ1FkBV7OBrs0aopibAiQDqLxNM2E3X"
filepath_json = f'/Users/radioproducer/Documents/verslibre-mixcloud/credentials.json'
dest_gd = "1XpVaubrDtdSaINGbzMbf7wrMMc_WrZu5"
delete_folder = "1WTTiocd8C5WUaYP4wTEMEshn-oKBxuRT"
origin_art = "1TEqe9SexwPpr8sVN9lzoZvozAYZGycRT0v4y9MRGD-fzvjrWB5qE7VesyBl8EdMCUtNj9SHc"
dest_art = "1ffVnNHXgFiqNVaeF3dJ0SyQnVcLuHcIr"
local_pre = "/Users/radioproducer/Documents/verslibre-mixcloud/prerec/pre/"
local_post = "/Users/radioproducer/Documents/verslibre-mixcloud/prerec/post/"
local_art = "/Users/radioproducer/Documents/verslibre-mixcloud/prerec/art/"
dest_macmini = "1CpEBqE49dEBmsJCsyrRa0M6u1EwpJF2t"

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

def download(file_id, file_name,dest):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(f"{dest}{file_name}", chunksize=1004857600)

drive = GoogleDrive(login_with_service_account()) # Create GoogleDrive instance with authenticated GoogleAuth instance

file_list_prec = drive.ListFile({'q': f"parents = '{prerec_folder_id}'"}).GetList()

for file in file_list_prec:
    id = file['id']
    title = file['title']
    file = drive.CreateFile({'id': file['id']})
    download(id,title,local_pre)
    move(id,delete_folder)

file_list_art = drive.ListFile({'q': f"parents = '{origin_art}'"}).GetList()
for file in file_list_art:
    id = file['id']
    title = file['title']
    file = drive.CreateFile({'id': file['id']})
    download(id,title,local_art)
    move(id,delete_folder)



def ts():
    currentDateAndTime = datetime.now()
    currentTime = currentDateAndTime.strftime("%H%M%S")
    return currentTime

def convert(file_name,new_path,old_path):
    trim_file_name, file_ext = os.path.splitext(file_name)
    new_name = f"{trim_file_name}-converted.mp3"
    new_path = f"{new_path}{new_name}"
    old_path = f"{old_path}{file_name}"

    AudioSegment.from_file(old_path).export(new_path, format="mp3", bitrate="320k")
    os.remove(old_path)
    return new_path

def upload_prec(src_path, dest_dir,file_name,type_mime='audio/mpeg'):
    metadata = {
        'parents': [
            {"id": dest_dir}
        ],
        'title': file_name,
        'mimeType': type_mime
    }
    file_new = drive.CreateFile(metadata)
    file_new.SetContentFile(src_path)
    file_new.Upload()

file_list=[f for f in os.listdir(local_pre) if not f.startswith('.')]
if len(file_list) == 0:
    logger.info(f"No files to process")
else:
    for file_name in file_list:
        time = ts()
        new_filename = f"{time}_{file_name}"
        new_path = convert(file_name, local_post,local_pre)
        upload_prec(new_path, dest_gd,file_name)
        upload_prec(new_path, dest_macmini,file_name)
        os.remove(new_path)
        logger.info(f"Finished converting sound for {new_filename}")


from PIL import Image

def convert_image(filepath):
    im = Image.open(filepath)
    file_name, file_ext = os.path.splitext(filepath)
    new_filename = f'{file_name}.png'
    im.save(new_filename)
    return new_filename
    


file_list=[f for f in os.listdir(local_art) if not f.startswith('.')]
if len(file_list) == 0:
    logger.info(f"No artword to process")
else:
    for file_name in file_list:
        path_art = f"{local_art}{file_name}"
        path_art_new = convert_image(path_art)
        new_file_name = os.path.basename(path_art_new)
        upload_prec(path_art_new,dest_art,new_file_name,"image/png")
        os.remove(path_art)
        os.remove(path_art_new)