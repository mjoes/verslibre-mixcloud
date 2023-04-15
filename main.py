import requests
import pandas as pd
import numpy as np
from pathlib import Path
import os
from datetime import datetime, timedelta
import time
from google.colab import drive
import shutil
drive.mount('/content/gdrive', force_remount=True)
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import io

def trim_sound(filepath):  
    new_path = f"{filepath}-mx"
    trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
    trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
    strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))

    sound = AudioSegment.from_file(filepath)
    stripped = strip_silence(sound)
    out = stripped.fade_in(3000).fade_out(3000)
    out.export(new_path, format="mp3", bitrate="320k")

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

    if dj_name is not np.nan:
        name=f"{show_name} #{int(df_active['show nr'].iloc[0])} - w/ {dj_name}"
    else:
        name=f"{show_name} #{int(df_active['show nr'].iloc[0])}"
    return name, show_name

df = pd.read_excel('/content/gdrive/My Drive/Radio Programmes & Events/2023/show_data.xlsx')
path_of_the_directory = '/content/gdrive/My Drive/Radio Programmes & Events/2023/uploadFolder/'
new_path = '/content/gdrive/My Drive/Radio Programmes & Events/'
file_list=[f for f in os.listdir(path_of_the_directory) if not f.startswith('.')]
log=pd.DataFrame({'file':file_list})
log["Upload"] = np.nan

for file_name in file_list:
    try:
        tag = file_name.split('-',2)[1]
        df_active=df[df["tag"]==tag]
        picpath=df_active["picture"].iloc[0]
        
        date_rec = datetime.strptime(file_name.split(' ',2)[0], '%Y%m%d')
        month = date_rec.month
        year = date_rec.year

        publish_date = get_publish(date_rec)
        name, show_name = get_name(df_active, tag)

        data=df_active[['description','tags-0-tag','tags-1-tag','tags-2-tag','tags-3-tag','tags-4-tag']].dropna(axis=1, how='all').to_dict('records')
        payload=data[0]
        payload.update({'name':f"{name}",'publish_date':f'{publish_date}','disable_comments':True,'hide_stats':True})

        # src_path = trim_sound(f'{path_of_the_directory}{file_name}')
        src_path = f'{path_of_the_directory}{file_name}'
        file = {
            #"mp3":trim_sound(f'{path_of_the_directory}{file_name}'),
            "mp3":open(src_path,'rb'),
            "picture":open(f"/content/gdrive/My Drive/Profiles/Radio Shows/{picpath}",'rb')
        }

        url = "https://api.mixcloud.com/upload/?access_token=xxx"

        response = requests.request("POST", url,data=payload,files=file)
        print(response.text)
        if 'RateLimitException' in response.text:
            log.loc[log['file'] == file_name, 'Upload'] = 'failed'
            print("error")
            #time.sleep(800)
        else:
            log.loc[log['file'] == file_name, 'Upload'] = 'passed'
            # src_path = new_path#f'{path_of_the_directory}{file_name}'
            dst_dir = f'{new_path}{year}/{month}/{show_name}'
            dst_path = f'{new_path}{year}/{month}/{show_name}/{file_name}'
            Path(dst_dir).mkdir(parents=True, exist_ok=True)
            shutil.move(src_path, dst_path)
            os.remove(f'{path_of_the_directory}{file_name}')
            df.loc[df['tag'] == tag, 'show nr'] = df.loc[df['tag'] == tag, 'show nr']+1
            df.to_excel(r'/content/gdrive/My Drive/Radio Programmes & Events/2023/show_data.xlsx', index = False)
    except:
        log.loc[log['file'] == file_name, 'Upload'] = 'failed'
        pass
        
print(log)