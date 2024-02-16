import os
import sys
import gspread
import pandas as pd
from loguru import logger

from mixcloud.config import local_upload, filepath_json, folderid_profiles, drive
from mixcloud.trimming import trimming
from mixcloud.upload import upload

logger.info("Starting audio processing")

SHEET_ID="1j2w0MPDL0R9Z_9XE5G_luDo4PgPEWhf6RNhwbxh7lmw"
SHEET_NAME="meta"                                                                                                                                  
gc = gspread.service_account(filename=filepath_json)
spreadsheet = gc.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)
rows = worksheet.get_all_records()
df = pd.DataFrame.from_dict(rows)

def run():
    file_list_profiles=trimming(df)
    upload_file_list=[f for f in os.listdir(local_upload) if not f.startswith('.')]
    #file_list_profiles = drive.ListFile({'q': f"parents = '{folderid_profiles}'"}).GetList()
    upload(df, worksheet, upload_file_list, file_list_profiles)

if __name__ == "__main__":
   run()