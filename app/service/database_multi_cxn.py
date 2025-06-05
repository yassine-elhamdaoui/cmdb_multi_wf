import configparser
from app.data import DATA_ORACLEDB, DB_ENV, data_directory
from app.util import osutil
import oracledb
import json
import os
import subprocess
import app.util

#["cmdb","bizops"], ["pswd1","pswd2"]
class database_multi_cxn:
    database_service_name :str
    database_host :str
    database_port :int
    dsn_name : str
    #if wallet
    tns_name : str
    wallet_password : str
    tns_admin : str


    def __init__(self):
        self.pools = {}
        self.load_dbdetails()


    def load_dbdetails(self):

        config = configparser.ConfigParser()

        # Read the configuration file
        orclconn_file_path = osutil.get_file_path(data_directory, DATA_ORACLEDB)
        orclenv_file_path = osutil.get_file_path(data_directory, DB_ENV)

        if osutil.does_file_exist(orclenv_file_path):
            print("Local wallet based connection code here.")
            #load_dotenv(orclenv_file_path)
            print(os.getenv("DB_USERNAME_LIST"))
            self.database_users = json.loads(os.getenv("DB_USERNAME_LIST"))
            self.database_passwords = json.loads(os.getenv("DB_PASSWORD_LIST"))
            self.tns_name = os.getenv("TNS_NAME")
            self.wallet_password = os.getenv("DB_WALLET_PASSWORD")
            self.tns_admin = os.getenv("TNS_ADMIN")
            self.dsn_name = self.tns_name

            print(self.database_users)
            print(self.database_passwords)
            print(self.tns_name)
            print(self.wallet_password)
            print(osutil.does_file_exist(self.tns_admin))
            print(self.tns_admin)
            print(self.tns_admin)
            config_dir = self.tns_admin
            wallet_location = self.tns_admin

            if len(self.database_users) != len(self.database_passwords):
                raise ValueError("The number of usernames and passwords do not match") 

            for username,password in zip(self.database_users, self.database_passwords):
                print(f"Connecting user: {username}")
                print(f"Password: {password}")
                self.create_pool_wallet(config_dir, wallet_location, self.wallet_password, username, password)

        elif osutil.does_file_exist(orclconn_file_path):
            config.read(orclconn_file_path) #'myoracle.cnf'
            # Get the values from config file
            self.database_host = config.get('DATABASE', 'host')
            self.database_port = config.get('DATABASE', 'port')
            self.database_service_name = config.get('DATABASE', 'service_name')
            self.database_users = json.loads(config.get('DATABASE', 'user'))
            self.database_passwords = json.loads(config.get('DATABASE', 'password'))
            self.dsn_name = f'{self.database_host}:{self.database_port}/{self.database_service_name}'
            if len(self.database_users) != len(self.database_passwords):
                raise ValueError("The number of usernames and passwords do not match") 

            for username,password in zip(self.database_users, self.database_passwords):
                print(f"Connecting user: {username}")
                print(f"Password: {password}")
                self.create_pool(username, password)


        else:            
            print("Wallet based connection code here.")
            print(os.getenv("DB_USERNAME_LIST"))
            print(os.getenv("DB_PASSWORD_LIST"))
            print(os.getenv('ACCESS_TOKEN_URL'))
            self.database_users = json.loads(os.getenv("DB_USERNAME_LIST"))
            self.database_passwords = json.loads(os.getenv("DB_PASSWORD_LIST"))
            self.tns_name = os.getenv("SERVICE_NAME") #TNS_NAME
            self.wallet_password = os.getenv("WALLET_PASSWORD") #DB_WALLET_PASSWORD
            self.tns_admin = os.getenv("TNS_ADMIN")
            self.dsn_name = self.tns_name

            print(self.database_users)
            print(self.database_passwords)
            print(self.tns_name)
            print(self.wallet_password)
            print(self.tns_admin)


            osutil.get_all_env()
            
            config_dir = self.tns_admin
            wallet_location = self.tns_admin
            
            if len(self.database_users) != len(self.database_passwords):
                raise ValueError("The number of usernames and passwords do not match") 

            for username,password in zip(self.database_users, self.database_passwords):
                print(f"Connecting user: {username}")
                print(f"Password: {password}")
                self.create_pool_wallet(config_dir, wallet_location, self.wallet_password, username, password)

        

    # Database Connection Pool 
    def create_pool(self, username, password):
        print("create_pool code here.")
        pool = oracledb.SessionPool(user=username, password=password, dsn=self.dsn_name, min=2, max=10, increment=1)
        self.pools[username] = pool

    # Database Connection Pool 
    def create_pool_wallet(self, config_dir, wallet_location, wallet_password,username, password ):
        print("create_pool_wallet code here.")
        pool = oracledb.SessionPool(user=username, password=password, 
                                         dsn=self.dsn_name, 
                                         config_dir=config_dir,
                                         wallet_location=wallet_location,
                                         wallet_password=wallet_password,
                                         min=2, max=10, increment=1)
        self.pools[username] = pool

    #includes context code to self release
    def get_db_conn(self, username):
        pool = self.pools.get(username)
        if pool is None:
            raise ValueError(f"No pool for user:{username}")
        with pool.acquire() as conn:
            yield conn


    #use for all other, has to be released
    def get_otherdb_conn(self, username):
        pool = self.pools.get(username)
        if pool is None:
            raise ValueError(f"No pool for user:{username}")
        conn = pool.acquire()
        return conn

    def release_conn(self, conn):
        if conn is None:
            raise ValueError(f"Invalid Connection asked to release")
        username_l = conn.username
        pool = self.pools.get(username_l)
        if pool is None:
            raise ValueError(f"No pool for user:{username_l}")
        else:
            conn = pool.release(conn)

    def close_pools(self):
        for pool in self.pools.values():
            pool.close()

    #for graphql we need row dictionary(name lowercase,value) 
    def row_dict_convert(self, cursor):
        column_names = [col[0].lower() for col in cursor.description]
        def create_row(*args):
          return dict(zip(column_names, args))
        return create_row




#test function to call sqlplus
def test_sqlplus_connection(user, password, service_name):
    try:
        connect_string = f"{user}/{password}@{service_name}"

        cmd = f"echo exit | sqlplus -L {connect_string}"

        # Run the command
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # Check result
        if "Connected to:" in result.stdout:
            print("SQL*Plus connection successful!")
        else:
            print("SQL*Plus connection failed. Here's the output:")
            print(result.stdout)
    except Exception as e:
        print(f"An error occurred: {e}")





