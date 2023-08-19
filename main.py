import requests
from mutagen.easyid3 import EasyID3
import mutagen
import pandas as pd
import numpy as np
from pathlib import Path
import os
from datetime import datetime, timedelta
import shutil
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import io
import gspread
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from loguru import logger
import sys

SHEET_ID="1j2w0MPDL0R9Z_9XE5G_luDo4PgPEWhf6RNhwbxh7lmw"
SHEET_NAME="meta"
filepath_json = f'/Users/radioproducer/Documents/verslibre-mixcloud/credentials.json'
local_base_path = '/Users/radioproducer/Documents/verslibre-mixcloud'
folderid_profiles = "1t7JgNd4U1oQEYw4NTdHPUFAIxd9YJWq3"

logger.info("Starting audio processing")

def download_picture(file_id, file_name):
    file = drive.CreateFile({'id': file_id})
    local_picture_path = f"{local_base_path}/picture/{file_name}"
    file.GetContentFile(local_picture_path, chunksize=1004857600)
    return local_picture_path
def trim_sound(file_name,filepath,tmp_path):  
    trim_file_name=file_name.split('.',2)[0]
    new_name = f"{trim_file_name}-mx.mp3"
    new_path = f"{filepath}{new_name}"
    file_path = f"{tmp_path}{file_name}"
    try:
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))
        sound = AudioSegment.from_file(file_path)
        stripped = strip_silence(sound)
        out = stripped.fade_in(3000).fade_out(3000)
        out.export(new_path, format="mp3", bitrate="320k")
    except:
        logger.info(f"FAILED: Trim and fade in/out for: {file_name}")
        shutil.copyfile(file_path, new_path)
    else:
        logger.info(f"PASSED: Trim and fade in/out for: {file_name}")

    os.remove(f'{local_base_path}/tmp/{file_name}')
    return new_path
def get_publish(date_rec):
    exp_date = date_rec + timedelta(days=1)
    if exp_date < datetime.today():
        publish_date=(datetime.today()+timedelta(days=1)).strftime("%Y-%m-%dT10:00:00Z")
    else:
        publish_date=exp_date.strftime("%Y-%m-%dT10:00:00Z")
    return publish_date
def get_name(df_active, tag):
    show_name = df_active['show_name'].iloc[0]
    dj_name = df_active['dj_name'].iloc[0]

    if dj_name != "":
        name=f"{show_name} #{int(df_active['show_nr'].iloc[0])} - w/ {dj_name}"
    else:
        name=f"{show_name} #{int(df_active['show_nr'].iloc[0])}"
    return name, show_name
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

def metadata(filePath, title, artist, genre, epNr, date):

    try:
        meta = EasyID3(filePath)
    except mutagen.id3.ID3NoHeaderError:
        meta = mutagen.File(filePath, easy=True)
        meta.add_tags()
    meta['title'] = title
    meta['artist'] = artist
    meta['genre'] = genre
    meta['tracknumber'] = str(epNr)
    meta['date'] = str(date)
    meta.save(filePath, v2_version=3)                                                                                                                                                       

drive = GoogleDrive(login_with_service_account())

gc = gspread.service_account(filename=filepath_json)
spreadsheet = gc.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)
rows = worksheet.get_all_records()
df = pd.DataFrame.from_dict(rows)

dest_dir="1-W9mP7aMI3u1A2fwXkrdblsjupk6PFeb"
local_temp=f"{local_base_path}/tmp/"
local_upload=f'{local_base_path}/upload/'
local_profiles=f"{local_base_path}/Profiles/"
file_list=[f for f in os.listdir(local_temp) if not f.startswith('.')]
upload_file_list=[f for f in os.listdir(local_upload) if not f.startswith('.')]
file_list_profiles = drive.ListFile({'q': f"parents = '{folderid_profiles}'"}).GetList()

if len(file_list) == 0:
    logger.info(f"No files to trim")
else:
    for file_name in file_list:
        logger.info(f"Starting trimming sound for {file_name}")
        trim_sound(file_name, local_upload,local_temp)

logger.info(f"Finished trimming stage")

upload_file_list=[f for f in os.listdir(local_upload) if not f.startswith('.')]

for file_name in upload_file_list:
    logger.info(f"Starting uploading stage for {file_name}")
    tag = file_name.split('-',2)[1]
    df_active=df[df["tag"]==tag]

    picpath=df_active["picture"].iloc[0]

    for file in file_list_profiles:
        if file['title'] == picpath:
            local_picpath = download_picture(file["id"],file['title'])
    

    date_rec = datetime.strptime(file_name.split(' ',2)[0], '%Y%m%d')
    month = date_rec.month
    year = date_rec.year

    publish_date = get_publish(date_rec)
    name, show_name = get_name(df_active, tag)

    data=df_active[['description','tags-0-tag','tags-1-tag','tags-2-tag','tags-3-tag','tags-4-tag']].dropna(axis=1, how='all').to_dict('records')
    payload=data[0]
    payload.update({'name':f"{name}",'publish_date':f'{publish_date}','disable_comments':True,'hide_stats':True})
    
    src_path = f"{local_upload}{file_name}"
 #   src_path = f"{local_upload}{file_name.split('-',2)[0]}-{tag}-{df_active['show_name'].iloc[0]}-{df_active['dj_name'].iloc[0]}-{df_active['show_nr'].iloc[0]}.mp3"
  #  os.rename(org_path, src_path)

   # metadata(src_path, df_active["show_name"].iloc[0], df_active["dj_name"].iloc[0], df_active["tags-0-tag"].iloc[0], df_active["show_nr"].iloc[0], year)

    try:
        file = {
            "mp3":open(src_path,'rb'),
            "picture":open(local_picpath,'rb')
        }
    except:
        logger.info("Failed to load picture or audio")
        continue

    url = "https://api.mixcloud.com/upload/?access_token=RTkqGEYJLEQaXVD54s6jA24jDJcM6GPz"
    try:
        logger.info(f"Upload {file_name} to Mixcloud")
        response = requests.request("POST", url,data=payload,files=file)
        response.raise_for_status()
        

        logger.info(f"Upload to mixcloud {file_name} PASSED")
        metadata = {
            'parents': [
                {"id": dest_dir}
            ],
            'title': file_name,
            'mimeType': 'audio/mpeg'
        }
        file_new = drive.CreateFile(metadata)
        file_new.SetContentFile(src_path)
        file_new.Upload()

        df.loc[df['tag'] == tag, 'show_nr'] = df.loc[df['tag'] == tag, 'show_nr']+1
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

        os.remove(src_path)
        os.remove(local_picpath)
        logger.info(f"Removed local files for: {file_name}")

    except Exception as error:
        logger.info(f"Upload {file_name} to failed")
        logger.info(error) 

        if 'RateLimitException' in "test":#response.text:
            logger.info("RateLimit Exception, break program")
        break

logger.info(f"Upload complete")