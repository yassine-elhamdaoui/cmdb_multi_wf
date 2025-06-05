import requests
import json
import os
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, HTTPError
import oracledb
import base64
from app.util.osutil import getsql_operations    
from app.service import myorcldb
from urllib.parse import urlparse, urljoin



async def purge_api_cache(wf_task_id,wf_run_id,wf_name,db_connection):
    print(f"{wf_name}:{wf_run_id}:purge_api_cache")

    try:
            
        cursor = db_connection.cursor()

        delete_query = """
        delete from api_cache where cached_date < sysdate -1
        """
        cursor.execute(delete_query)
        db_connection.commit()

    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        exception_message = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exception_message = str(e)
    finally:
      cursor.close()



#ADD_ORGOCIDS_CSS_CUSTOMER_STAGE
async def call_api_csscustomer_stage(wf_task_id,wf_run_id,wf_name,db_connection):
    print(f"{wf_name}:{wf_run_id}:call_api_csscustomer_cache")
    progress_log = ""
    result = None
    exception_message = None

    try:
            
        cursor = db_connection.cursor()

        exec_query = """
        declare 
        result_set VARCHAR2(10);
        BEGIN
            select decode(TO_CHAR(SYSTIMESTAMP AT TIME ZONE 'US/Eastern','HH24'), '01','Y','N') into result_set from dual;
            IF result_set = 'Y' THEN
                ADD_ORGOCIDS_CSS_CUSTOMER_STAGE;
            END IF;
        END;
        """
        cursor.execute(exec_query)
        db_connection.commit()
        result = "Success."
        progress_log = "Success."
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        exception_message = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exception_message = str(e)
    finally:
      cursor.close()


    result_dict = {"progress": progress_log,
            "result": result,
            "exception": exception_message}
    result_json = json.dumps(result_dict,default=str)
    return result_json