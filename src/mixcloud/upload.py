import requests
import gspread
import pandas as pd
import os

from loguru import logger
from datetime import datetime, timedelta

from mixcloud.utils import download_picture, get_publish, get_name, get_metadata
from mixcloud.config import local_upload, dest_dir, drive, filepath_json
from mixcloud.metadata import add_metadata_to_mp3

API_KEY = os.getenv('API_KEY')

def upload(df, worksheet, upload_file_list, file_list_profiles):
    for file_name in upload_file_list:
        logger.info(f"Starting uploading stage for {file_name}")
        tag = file_name.split('_',2)[1]
        df_active=df[df["tag"]==tag]
        picpath=df_active["picture"].iloc[0]
        for file in file_list_profiles:
            if file['title'] == picpath:
                local_picpath = download_picture(file["id"],file['title'])
        

        date_rec = datetime.strptime(file_name.split('_',2)[0], '%Y%m%d')
        year = date_rec.year 

        publish_date = get_publish(date_rec)
        name, show_name = get_name(df_active, tag, date_rec)

        data=df_active[['description','tags-0-tag','tags-1-tag','tags-2-tag','tags-3-tag','tags-4-tag']].dropna(axis=1, how='all').to_dict('records')
        payload=data[0]
        payload.update({'name':f"{name}",'publish_date':f'{publish_date}','disable_comments':True,'hide_stats':True})
        
        src_path = f"{local_upload}{file_name}"

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
            logger.error(f"Upload to Mixcloud {file_name} failed: {error}")
            logger.error(response.text)

            if 'RateLimitException' in response.text:
                logger.info("RateLimit Exception, break program")
            break
        try:
            show_name, dj_name, ep_nr, genre = get_metadata(df_active)
            add_metadata_to_mp3(src_path, show_name, dj_name, ep_nr, genre, year)
            filename=os.path.basename(src_path)
            metadata = {
                'parents': [
                    {"id": dest_dir}
                ],
                'title': filename,
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