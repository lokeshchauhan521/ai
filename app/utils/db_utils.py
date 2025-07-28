# import os
# import sys

# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from utils.database import Db
from utils.logger import FileLogs
from utils.s3_utils import delete_folder
import os

logs = FileLogs().get_logger(os.path.basename(__file__))

def regenerate_summary(product_id):
    try:
        result = False
        cscan_document_filename_query = f"SELECT productID, document_filename FROM cscan_document WHERE productID = {product_id}"
        conn = Db().get_connection_product()
        curs = conn.cursor(buffered=True, dictionary=True)
        curs.execute(cscan_document_filename_query)
        cscan_document_filename_data= curs.fetchone()
        cscan_product_summary_filename_query = f"SELECT product_id, document_filename FROM cscan_product_summary WHERE product_id = {product_id}"
        curs.execute(cscan_product_summary_filename_query)
        cscan_product_summary_filename_data= curs.fetchone()

        if cscan_document_filename_data.get("document_filename", "cscan_document") !=  cscan_product_summary_filename_data.get("document_filename", "cscan_product_summary"):
            delete_query = f"delete from cscan_product_summary where product_id= {product_id}"
            curs.execute(delete_query)
            status = delete_folder(product_id)
            conn.commit()
            logs.info(f"deleting s3 folder for product id {product_id} --> {status}")
            result = True
        curs.close()
        conn.close()
        return result
    except Exception as e:
        logs.error("Error occured in fetching regen_summary", exc_info=1)
        return None

def get_product_text(product_id):
    try:

        query = f"SELECT productID, dts_val FROM cscan_document_text_search WHERE productID = {product_id}"
        conn = Db().get_connection_product()
        curs = conn.cursor(buffered=True, dictionary=True)
        curs.execute(query)
        data= curs.fetchone()
        curs.close()
        conn.close()
        return data.get("dts_val")
    except Exception as e:
        logs.error("Error occured in fetching dts val data", exc_info=1)
        return None
    
def get_db_summary(product_id):
    try:

        query = f"SELECT product_id, summary FROM cscan_product_summary WHERE product_id = {product_id}"
        conn = Db().get_connection_product()
        curs = conn.cursor(buffered=True, dictionary=True)
        curs.execute(query)
        data= curs.fetchone()
        curs.close()
        conn.close()
        if data==None:
            return None
        else:
            return data.get("summary")
    except Exception as e:
        logs.error("Error occured in fetching summary data", exc_info=1)
        return None
    
    
def insert_db_summary(product_id, summary):
    try:

        query = "Insert into cscan_product_summary (product_id, summary,document_filename) values (%s, %s, %s)"
        conn = Db().get_connection_product()
        curs = conn.cursor(buffered=True, dictionary=True)

        document_filename_query = f"SELECT productID, document_filename FROM cscan_document WHERE productID = {product_id}"
        curs.execute(document_filename_query)
        file_data = curs.fetchone()
        document_filename = file_data.get("document_filename", "")
        logs.info(f"document filename is {document_filename}")
        value = (product_id, summary,document_filename)
        curs.execute(query, value)
        conn.commit()
        curs.close()
        conn.close()
        return True
    except Exception as e:
        print(e)
        logs.error("Error occured in inserting summary data", exc_info=1)
        return None
    
if __name__ == "__main__":
    print(get_product_text(128))

