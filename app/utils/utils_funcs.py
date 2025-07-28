# import os
# import sys

# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import os
from utils.constants import PDF_URL
import shutil
import requests
from utils.logger import FileLogs

logs = FileLogs().get_logger(os.path.basename(__file__))

def get_pdf_file(product_id):
    pdfpath = f"{product_id}.pdf"
    folder_path = os.path.join(os.getcwd(), "tmp_files")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    filepath = os.path.join(folder_path, pdfpath)
    if not os.path.exists(filepath):
        data = requests.get(f"{PDF_URL}{product_id}")
        with open(filepath, "wb") as file:
            file.write(data.content)

    return filepath

def get_topic_key(product_id, user_id):
    return f"{user_id}8888{product_id}"

def cleanup_space(product_id):
    pdf_file_path = f"tmp_files/{product_id}.pdf"
    if os.path.exists(pdf_file_path):
        os.remove(pdf_file_path)
    chroma_files_path = f"chroma_files/{product_id}"
    try:
        shutil.rmtree(chroma_files_path)
    except FileNotFoundError:
        logs.error(f"Folder {chroma_files_path} does not exist.")
    except PermissionError:
        logs.error(f"Permission denied to delete {chroma_files_path}.")
    except Exception as e:
        logs.error(f"An error occurred: {e}", exc_info=1)


    
if __name__ == "__main__":
    import requests
    data = requests.get("https://api2.competiscan.com/product/v1/openpdf?product_type=ProductImg&product_id=138")
    with open("tmp_files/test.pdf", "wb") as file:
        file.write(data.content)
    # bucket_name , filepath = get_pdf_s3_path(211)
    # print(bucket_name +"------"+ filepath)
    # bucket = S3Bucket(BUCKET_NAME=bucket_name, PROFILE_NAME="csv2-emailcontent-development")
    # local_path = os.path.join(os.getcwd(), "tmp_files", "file.pdf")
    # bucket.download_s3_file(filepath, local_path)

