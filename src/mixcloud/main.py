import os
import sys
from loguru import logger

from mixcloud.config import local_upload
from mixcloud.trimming import trimming
from mixcloud.upload import upload

logger.info("Starting audio processing")


def run():
    file_list_profiles=trimming()
    upload_file_list=[f for f in os.listdir(local_upload) if not f.startswith('.')]
    upload(upload_file_list, file_list_profiles)

if __name__ == "__main__":
   run()