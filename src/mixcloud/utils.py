from mixcloud.config import drive, local_base_path
from datetime import datetime, timedelta

def download_picture(file_id, file_name):
    file = drive.CreateFile({'id': file_id})
    local_picture_path = f"{local_base_path}/picture/{file_name}"
    file.GetContentFile(local_picture_path, chunksize=1004857600)
    return local_picture_path

def get_publish(date_rec):
    exp_date = date_rec + timedelta(days=1)
    if exp_date < datetime.today():
        publish_date=(datetime.today()).strftime("%Y-%m-%dT10:00:00Z")
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