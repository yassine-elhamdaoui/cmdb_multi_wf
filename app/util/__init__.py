from dotenv import load_dotenv
import os
from app.util import osutil
from app.data import DATA_ORACLEDB, DB_ENV, data_directory

orclenv_file_path = osutil.get_file_path(data_directory, DB_ENV)
if osutil.does_file_exist(orclenv_file_path):
    load_dotenv(orclenv_file_path)