import requests
import gspread
import pandas as pd
import os

from loguru import logger
from datetime import datetime, timedelta

from mixcloud.utils import download_picture, get_publish, get_name
from mixcloud.config import local_upload, dest_dir, drive, filepath_json
from mixcloud.metadata import metadata

API_KEY = os.getenv('API_KEY')
SHEET_ID="1j2w0MPDL0R9Z_9XE5G_luDo4PgPEWhf6RNhwbxh7lmw"
SHEET_NAME="meta"                                                                                                                                  
gc = gspread.service_account(filename=filepath_json)
spreadsheet = gc.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)
rows = worksheet.get_all_records()
df = pd.DataFrame.from_dict(rows)

def upload(upload_file_list, file_list_profiles):
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

    #    metadata(src_path, df_active["show_name"].iloc[0], df_active["dj_name"].iloc[0], df_active["tags-0-tag"].iloc[0], df_active["show_nr"].iloc[0], year)

        try:
            file = {
                "mp3":open(src_path,'rb'),
                "picture":open(local_picpath,'rb')
            }
        except Exception as error:
            logger.info(f"Failed to load picture or audio: {error}")
            continue

        url = f"https://api.mixcloud.com/upload/?access_token={API_KEY}"
        try:
            response = requests.request("POST", url=url,data=payload,files=file)
            response.raise_for_status()
            logger.info(f"Upload to Mixcloud {file_name} PASSED")
        except Exception as error:
            logger.info(f"Upload to Mixcloud {file_name} failed: {error}")
            print(response.raise_for_status())

            if 'RateLimitException' in response.text:
                logger.info("RateLimit Exception, break program")
            break
        try:
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

            logger.info(f"Upload to Google Drive {file_name} PASSED")
            os.remove(src_path)
            os.remove(local_picpath)
            logger.info(f"Removed local files for: {file_name}")
        except Exception as error:
            logger.info(f"Upload to Google Drive and cleanup of {file_name} failed: {error}")

    logger.info(f"Program complete")