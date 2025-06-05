from app.util.osutil import getsql_operations
from app.service import myorcldb
import os
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, HTTPError

sql_queries = getsql_operations("sql_wf.yaml")

# Checks if the WF tables are there, if not creates them
def check_and_create_wf_tables(conn): 
    # SQL statements to check if tables exist
    check_workflow_runs_table = sql_queries["check_workflow_runs_table"] 
    check_workflow_tasks_table = sql_queries["check_workflow_tasks_table"] 

    # SQL statements to create tables if they don't exist
    create_workflow_runs_table = sql_queries["create_workflow_runs_table"] 

    create_workflow_tasks_table = sql_queries["create_workflow_tasks_table"] 

    with conn.cursor() as cursor:
        # Check and create workflow_runs table
        cursor.execute(check_workflow_runs_table)
        if cursor.fetchone()[0] == 0:
            cursor.execute(create_workflow_runs_table)

        # Check and create workflow_tasks table
        cursor.execute(check_workflow_tasks_table)
        if cursor.fetchone()[0] == 0:
            cursor.execute(create_workflow_tasks_table)

    conn.commit()



def add_workflow_run(conn, workflow_name, execution_date, state):

    add_workflow_run = sql_queries["add_workflow_run"] 
    new_id = conn.cursor().var(int)
    with conn.cursor() as cursor:
        cursor.execute(add_workflow_run, (workflow_name,execution_date,state, new_id))
        #new_id = cursor.fetchone()[0] # Fetch the generated ID
    conn.commit()
    return new_id.getvalue()[0]


def add_workflow_task(conn, task_name, workflow_run_id, task_type, state, start_time, end_time):
    add_workflow_task = sql_queries["add_workflow_task"] 
    new_id = conn.cursor().var(int)
    with conn.cursor() as cursor:
        cursor.execute(add_workflow_task, (task_name, workflow_run_id, task_type, state, start_time, end_time,new_id) )
        #new_id = cursor.fetchone()[0] # Fetch the generated ID
    conn.commit()
    return new_id.getvalue()[0]

#workflow_runs.id=workflow_run_id
def update_workflow_run(conn, workflow_run_id, new_state):
    update_workflow_run = sql_queries["update_workflow_run"] 
    with conn.cursor() as cursor:
        cursor.execute(update_workflow_run, (new_state, workflow_run_id) )
    conn.commit()

#workflow_tasks.id=task_id
def update_workflow_task(conn, task_id, new_state, result=None):
    if result is not None:
        update_workflow_task = sql_queries["update_workflow_task_result"] 
        params = [new_state,new_state,result,task_id]
    else:
        update_workflow_task = sql_queries["update_workflow_task"] 
        params = [new_state,new_state,task_id]

    with conn.cursor() as cursor:
        cursor.execute(update_workflow_task,params )
    conn.commit()

#workflow_runs.workflow_name=workflow_name
#if >0 => atleast one instance running
def exists_workflow_run(conn, workflow_name):
    count_wf_run = sql_queries["exists_workflow_run"] 
    with conn.cursor() as cursor:
        cursor.execute(count_wf_run,{'workflow_name':workflow_name})
        result = cursor.fetchone()
        return result[0]==1
    
#workflow_tasks.task_name=task_name
def exists_workflow_task(conn, task_name):
    count_wf_run = sql_queries["exists_workflow_run"] 
    with conn.cursor() as cursor:
        cursor.execute(count_wf_run,{'task_name':task_name})
        result = cursor.fetchone()
        return result[0]==1

#workflow_runs.id=workflow_id
def get_last_workflow_run(conn, workflow_name):
    last_run = sql_queries["get_last_workflow_run"] 
    with conn.cursor() as cursor:
        cursor.execute(last_run,{'workflow_name':workflow_name})
        result = cursor.fetchone()
        #return result['last_execution_date'] if result else None        
        return result[0] if result else None
    

#pass a taskid, find wf_run and look for result for taskname
def get_workflow_task_result(conn, wf_task_id, result_oftask_name):
    task_result = sql_queries["get_workflow_task_result"] 
    with conn.cursor() as cursor:
        cursor.execute(task_result,(wf_task_id, result_oftask_name))
        result = cursor.fetchone()
        return result[0] if result else None
    
def get_access_token() -> str:
    try:
        # Retrieve environment variables
        token_url = os.getenv('ACCESS_TOKEN_URL')
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        scope = os.getenv('SCOPE')
        
        # Check if all required environment variables are set
        if not all([token_url, client_id, client_secret, scope]):
            missing_vars = [var for var in ['ACCESS_TOKEN_URL', 'CLIENT_ID', 'CLIENT_SECRET', 'SCOPE'] if os.getenv(var) is None]
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