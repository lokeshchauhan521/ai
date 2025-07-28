import mysql.connector
import os
from dotenv import load_dotenv
from utils.logger import FileLogs


load_dotenv()
logs = FileLogs().get_logger()
class Db:
    def __init__(self):

        self.conn_product = None
        # get db cred from .env file
        self.HOST_NAME_COMP = os.environ['HISTORICAL_HOST']
        self.USER_COMP = os.environ['HISTORICAL_USERNAME']
        self.PASSWORD_COMP = os.environ['HISTORICAL_PASSWORD']
        self.DATABASE_PRODUCT = os.getenv('HISTORICAL_CSV2_PRODUCT')

    # connection for product db
    def get_connection_product(self):
        if self.conn_product is None:
            try:
                self.conn_product = mysql.connector.connect(
                    host = self.HOST_NAME_COMP,
                    database = self.DATABASE_PRODUCT,
                    user = self.USER_COMP,
                    password = self.PASSWORD_COMP,
                    auth_plugin = 'mysql_native_password'
                )
            except Exception as e:
                logs.error("error in connection", exc_info=1)
                return None
        return self.conn_product
