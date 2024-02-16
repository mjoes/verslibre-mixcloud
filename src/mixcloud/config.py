from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

filepath_json = f'/Users/radioproducer/Documents/verslibre-mixcloud/credentials.json'
local_base_path = '/Users/radioproducer/Documents/verslibre-mixcloud'
folderid_profiles = "1t7JgNd4U1oQEYw4NTdHPUFAIxd9YJWq3"
local_temp=f"{local_base_path}/tmp/"
local_upload=f'{local_base_path}/upload/'
local_profiles=f"{local_base_path}/Profiles/"
dest_dir="1qklZQWVpNRYJWLd0-0zBhxZLyWCHrtpe"

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

drive = GoogleDrive(login_with_service_account())