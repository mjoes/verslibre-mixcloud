import shutil
import os
import pandas as pd

from loguru import logger
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from datetime import datetime
from mixcloud.config import folderid_profiles,local_temp, local_base_path, local_upload, drive
from mixcloud.utils import get_metadata, get_filename

from pathlib import Path
from pydub import AudioSegment

def trim_sound(file_name,filepath,tmp_path, filename_archive):  
    new_name = f"{filename_archive}.mp3"
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
    except Exception as e:
        logger.info(f"FAILED: Trim and fade in/out for: {file_name}")
        logger.error(e)
        shutil.copyfile(file_path, new_path)
    else:
        logger.info(f"PASSED: Trim and fade in/out for: {file_name}")

    os.remove(f'{local_base_path}/tmp/{file_name}')
    return new_path

def trimming(df):
    file_list=[f for f in os.listdir(local_temp) if not f.startswith('.')]
    upload_file_list=[f for f in os.listdir(local_upload) if not f.startswith('.')]
    file_list_profiles = drive.ListFile({'q': f"parents = '{folderid_profiles}'"}).GetList()

    if len(file_list) == 0:
        logger.info(f"No files to trim")
    else:
        for file_name in file_list:
            logger.info(f"Starting trimming sound for {file_name}")

            tag = file_name.split('-',2)[1]
            date = file_name.split(' ',2)[0]

            df_active=df[df["tag"]==tag]
            filename_archive = get_filename(tag, show_name, dj_name, ep_nr, date)

            trim_sound(file_name, local_upload,local_temp, filename_archive)

    logger.info(f"Finished trimming stage")
    return file_list_profiles