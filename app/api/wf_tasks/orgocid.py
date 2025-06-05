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

def get_access_token() -> str:

    try:

        # Retrieve environment variables
        token_url = os.getenv('ACCESS_TOKEN_URL')
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        scope = os.getenv('SCOPE')

        # Check if all required environment variables are set
        if not all([token_url, client_id, client_secret, scope]):
            missing_vars = [var for var in ['ACCESS_TOKEN_URL', 'CLIENT_ID', 'CLIENT_SECRET', 'SCOPE'] if
os.getenv(var) is None]
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

        # Prepare the request payload and headers
        payload = {
            'grant_type': 'client_credentials',
            'scope': scope
        }
 
        # Perform the request to get the access token
        response = requests.post(
            token_url,
            data=payload,
            auth=HTTPBasicAuth(client_id, client_secret)  # Client authentication using HTTP Basic Auth
        )
      

        # Raise HTTPError if the response was unsuccessful
        response.raise_for_status()




        # Parse the access token from the response
        token_data = response.json()
        access_token = token_data.get('access_token')
       

        if not access_token:
            raise ValueError("The response does not contain an access token.")

        return access_token

    

    except EnvironmentError as env_err:
        print(f"Environment error: {env_err}")
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except ValueError as val_err:
        print(f"Value error: {val_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None    


"""
takes a json data, first looks for winner_ocid which is !None, !inactive
if nothing, concats ocid where winner_ocid is !inactive
"""
def get_winner_ocid(data):

    if data and 'data' in data:
        # First, attempt to find a valid winner_ocid
        for entry in data['data']:
            winner_ocid = entry.get('winner_ocid')
            if (
                winner_ocid and
                isinstance(winner_ocid, str) and
                'inactive' not in winner_ocid.lower()
            ):
                return winner_ocid

        # If no valid winner_ocid is found, collect ids
        ids = []
        for entry in data['data']:
            winner_ocid = entry.get('winner_ocid')
            # Skip entries where winner_ocid is 'inactive' (case-insensitive)
            if winner_ocid and 'inactive' in winner_ocid.lower():
                continue  # Skip this entry
            # Collect the ocid from the entry if it exists and is a string
            id_value = entry.get('ocid')
            if id_value and isinstance(id_value, str):
                ids.append(id_value)
        # Concatenate the ids into a comma-separated string
        if ids:
            concatenated_ids = ','.join(ids)
            return concatenated_ids
        else:
            # If no ids are collected, return None
            return None
    else:
        # If data is None or doesn't contain 'data' key, return None
        return None

def trunc_str(s,length=5):
    return s[:length]+"..." if len(s) > length else s

def last_5_str(s,length=5):
    if not isinstance(s,str):
        return ""
    return s[-length:] if len(s) >= length else s 


def update_orgocid_status(cursor, capid, party_num, gpp_num, csi, orgocid):
    try:
        cursor.callproc("update_orgocid_status", [capid, party_num, gpp_num, csi, orgocid])
        print(f"Updated capid:{capid}, csi:{csi} with orgocid: {trunc_str(orgocid) if orgocid else 'FETCH FAILED'}")
    except Exception as e:
        print(f"Database error: {e}")

async def get_orgocid_for(wf_task_id,wf_run_id,wf_name,db_connection, n):
    print(f"{wf_name}:{wf_run_id}:get_orgocid_for")

    progress_log = ""
    result = None
    exception_message = None

    try:
            
        #conn = myorcldb.get_otherdb_conn()

        access_token = get_access_token()
        if access_token:
            print(f"Bearer Access Token: found")
            progress_log += "Bearer Access Token: found\n"
        else:
            print("Failed to retrieve access token.")
            progress_log+="Failed to retrieve access token.\n"
            raise ValueError("get_orgocid_for:The response does not contain an access token.")

        cursor = db_connection.cursor()

        select_query_old = f"""
        SELECT CAP_CUSTOMER_ID capid, PARTY_NUM party_number, GPP_NUM global_party_number, csi csi_number
        FROM csi_master
        WHERE orgocid IS NULL 
        FETCH FIRST {n} ROWS ONLY
        """
        
        select_query = f"""
        SELECT CAP_CUSTOMER_ID capid, PARTY_NUM party_number, GPP_NUM global_party_number, csi csi_number 
        FROM csi_master 
        WHERE orgocid_last_fetched_date <= SYSDATE - 30 
        AND orgocid_status IN ('ACTIVE', 'BACKOFF')
        FETCH FIRST 30 ROWS ONLY
        """


        cursor.execute(select_query)
        records = cursor.fetchall()
        result_set_sz= len(records)
        progress_log+=f"Got {result_set_sz} records in get_orgocid_for."
        field_mapping = {
            'cap_customer_id': 'capCustomerID',
            'party_num': 'gsiPartyNumber',
            'gpp_num': 'gsiPartyNumber',
            'csi': 'customerCSINumbers'
        }

        base_url = os.getenv('ORGOCID_URL')
        local =os.getenv("LOCAL")
        if local == "TRUE":
            url_template = urljoin(base_url, "/customer-master/v1/customers/.lookup?field_name={}&field_value={}")
        else:
            url_template = urljoin(base_url, "/v1/customers/.lookup?field_name={}&field_value={}")
        print(f"url_template: {url_template}")
        #base_url = "https://omcs-ssp2-dev.opc.oracleoutsourcing.com" #os.getenv('BASE_URL')
        #url_template = urljoin(base_url, "/customer-master/v1/customers/.lookup?field_name={}&field_value={}")
        #base_url = "http://customer-master.customer-master.svc.cluster.local"
        #url_template = urljoin(base_url, "/.lookup?field_name={}&field_value={}")
        #url_template = "http://...//.lookup?field_name={}&field_value={}"

        headers = {'Authorization': 'Bearer '+access_token}
        winner_ocid = None

        for record in records:
            record_dict = {
                'cap_customer_id': record[0],
                'party_num': record[1],
                'gpp_num': record[2],
                'csi': record[3]
            }

            for db_field, api_field in field_mapping.items():
                field_value = record_dict.get(db_field)
                if field_value:
                    url = url_template.format(api_field, field_value)
                
                    try:
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        data = response.json()
                        #print(f"{field_value}:{data}")

                        if data and 'data' in data:
                            #winner_ocid = next((entry.get('winner_ocid') for entry in data['data'] if entry.get('winner_ocid')), None)
                            winner_ocid = get_winner_ocid(data)

                            if winner_ocid:
                                miniwinner = last_5_str(winner_ocid)
                                print(f"winner_ocid:{miniwinner}")
                                update_orgocid_status(cursor, record[0], record[1], record[2], record[3], winner_ocid)
                                db_connection.commit()
                                break

                    except requests.RequestException as e:
                        print(f"get_orgocid_for:Request error: {e}")
                    except json.JSONDecodeError:
                        print("Error decoding JSON response")
                    except Exception as e:
                        print(f"Unexpected error: {e}")


            if not winner_ocid:
                update_orgocid_status(cursor, record[0], record[1], record[2], record[3], winner_ocid)
                db_connection.commit()
        
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        exception_message = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exception_message = str(e)
    finally:
      cursor.close()

    print(progress_log)
    result_dict = {"progress": progress_log,
            "result": result,
            "exception": exception_message}
    result_json = json.dumps(result_dict,default=str)
    return result_json

async def get_orgocid_details(wf_task_id,wf_run_id,wf_name,db_connection):
    print(f"{wf_name}:{wf_run_id}:get_orgocid_details")
    progress_log = ""
    result = None
    exception_message = None

    try:

        access_token = get_access_token()
        if access_token:
            print(f"Bearer Access Token found")
            progress_log = "Bearer Access Token found\n"
        else:
            print("Failed to retrieve access token.")
            progress_log = "Failed to retrieve access token.\n"
            raise ValueError("get_orgocid_for:The response does not contain an access token.")
        #conn = myorcldb.get_otherdb_conn()
        cursor = db_connection.cursor()

        """select_orgocid_query = 
        SELECT distinct orgocid
        FROM csi_master
        WHERE orgocid NOT IN (SELECT orgocid FROM ORGOCID_CUSTOMER_DETAILS)
        and orgocid is not null
        """

        select_orgocid_query = """
        select orgocidx orgocid from
        (
        select distinct orgocidx from csi_master csim, LATERAL
        (select  TRIM(REGEXP_SUBSTR(csim.orgocid,'[^,]+',1,LEVEL)) as  orgocidx from dual
        connect by level <= REGEXP_COUNT(csim.orgocid,',') +1)
        )
        WHERE orgocidx NOT IN (SELECT orgocid FROM ORGOCID_CUSTOMER_DETAILS)
        and orgocidx is not null
        """


        cursor.execute(select_orgocid_query)
        orgocid_records = cursor.fetchall()
        result_set_sz= len(orgocid_records)
        progress_log+=f"Got {result_set_sz} records in get_orgocid_details."


        base_url = os.getenv('ORGOCID_URL')
        local =os.getenv("LOCAL")
        if local == "TRUE":
            url_template = urljoin(base_url, "/customer-master/v1/customers/{}")
        else:
            url_template = urljoin(base_url, "/v1/customers/{}")
        #base_url = "http://customer-master.customer-master.svc.cluster.local"
        #url_template = "http://customer-master.customer-master.svc.cluster.local/{}"
        print(url_template)

        headers = {'Authorization': 'Bearer '+access_token}

        for orgocid_tuple in orgocid_records:
            orgocid_field = orgocid_tuple[0]
            orgocid_list = orgocid_field.split(',') #may be one or more comma seperated
            for orgocid in orgocid_list:
                orgocid=orgocid.strip()
                url = url_template.format(orgocid)

                try:
                    customer_data = None
                    try:
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        customer_data = response.json()
                    except requests.RequestException as e:
                        print(f"get_orgocid_details:Request error: {e}")
                        customer_data={}

                    json_data_str = json.dumps(customer_data)

                    select_query = """
                    SELECT COUNT(*)
                    FROM ORGOCID_CUSTOMER_DETAILS
                    WHERE orgocid = :1
                    """
                    
                    cursor.execute(select_query, (orgocid,))
                    record_exists = cursor.fetchone()[0] > 0

                    if record_exists:
                        update_query = """
                        UPDATE ORGOCID_CUSTOMER_DETAILS
                        SET customer_data = :1
                        WHERE orgocid = :2
                        """
                        cursor.execute(update_query, (json_data_str, orgocid))
                    else:
                        insert_query = """
                        INSERT INTO ORGOCID_CUSTOMER_DETAILS (orgocid, customer_data)
                        VALUES (:1, :2)
                        """
                        cursor.execute(insert_query, (orgocid, json_data_str))
                    
                    db_connection.commit()


                except json.JSONDecodeError:
                    print("Error decoding JSON response")
                except Exception as e:
                    print(f"Unexpected error: {e}")
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cursor.close()

    result_dict = {"progress": progress_log,
            "result": result,
            "exception": exception_message}
    result_json = json.dumps(result_dict,default=str)
    return result_json




async def set_regid_in_orgocid_details(wf_task_id,wf_run_id,wf_name,db_connection):
    print(f"{wf_name}:{wf_run_id}:set_regid_in_orgocid_details")

    progress_log = ""
    result = None
    exception_message = None

    try:

        cursor = db_connection.cursor()

        update_regid_in_orgocid_details_query = """
        update ORGOCID_CUSTOMER_DETAILS set
        REGISTRY_ID=json_value(customer_data, '$.customerRegistryID') 
        where REGISTRY_ID is NULL and customer_data is NOT NULL 
        """

        cursor.execute(update_regid_in_orgocid_details_query)
        db_connection.commit()

    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        exception_message = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exception_message = str(e)
    finally:
      cursor.close()