import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import boto3
from botocore.exceptions import NoCredentialsError
from utils.logger import FileLogs
from utils.constants import BUCKET_NAME, PROFILE_NAME

logs = FileLogs().get_logger() 

def upload_folder_to_s3(product_id):
    """
    :return: True or False
    """
    # Initialize a session using the specified profile
    session = boto3.Session(profile_name=PROFILE_NAME)
    s3_client = session.client('s3')
    folder_path = os.path.join("chroma_files", f"{product_id}")

    if not os.path.exists(folder_path):
        return False

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                # Upload the file
                s3_client.upload_file(local_file_path, BUCKET_NAME, local_file_path)

        return True
        
    except FileNotFoundError:
        logs.error("Error: The folder or a file in it was not found.")
        return False
    
    except NoCredentialsError:
        logs.error("Error: AWS credentials not found.")
        return False
    
    except Exception as e:
        logs.error(f"An error occurred: {e}")
        return False

def delete_folder(product_id):
    try:
        session = boto3.Session(profile_name=PROFILE_NAME)
        s3_resource = session.resource('s3')
        bucket = s3_resource.Bucket(BUCKET_NAME)
        folder_name = f"chroma_files/{product_id}"
        bucket.objects.filter(Prefix=folder_name).delete()
        return True
    except Exception as e:
        print(e)
        return False


def download_folder_from_s3(product_id):

    # Initialize a session using the specified profile
    session = boto3.Session(profile_name=PROFILE_NAME)
    s3_client = session.client('s3')
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket(BUCKET_NAME)
    local_folder_path = s3_folder_path = f"chroma_files/{product_id}"

    try:
        empty=True
        for obj in bucket.objects.filter(Prefix=s3_folder_path):
            # Skip folders (S3 keys ending with "/")
            if obj.key.endswith('/'):
                continue
            
            # Define the local path
            relative_path = os.path.relpath(obj.key, s3_folder_path)
            local_file_path = os.path.join(local_folder_path, relative_path)

            # Ensure the directory structure exists locally
            local_dir = os.path.dirname(local_file_path)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Download the file
            logs.info(f"Downloading {obj.key} to {local_file_path}")
            s3_client.download_file(BUCKET_NAME, obj.key, local_file_path)
            empty = False
            logs.info(f"Downoaded {obj.key} to {local_file_path}")

        logs.info("Folder downloaded successfully!")
        if empty:
            return False
        else:
            return True
    except NoCredentialsError:
        logs.error("Error: AWS credentials not found.")
        return False
    except Exception as e:
        logs.error(f"An error occurred: {e}")
        return False





if __name__ == "__main__":
    print(delete_folder(2765010))
