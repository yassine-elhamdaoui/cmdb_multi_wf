import json
import importlib
import asyncio
from datetime import datetime, timedelta
from dateutil.parser import parse
from app.wf.wf_util import add_workflow_run, add_workflow_task, update_workflow_run, update_workflow_task, get_last_workflow_run
from app.wf.node_task import PyNodeTask,PyStdNodeTask
from app.service import myorcldb
from app.wf import wf_util
from app.wf.wf_json_validate import validate_workflow_json
from app.util import osutil
import os
import app.util
from app.api.wf_tasks.standard import wait_task

# Function to read workflow JSON from a file
def read_workflow_json(workflow_json):
    is_valid, message = validate_workflow_json(workflow_json)

    if is_valid:
        print(f"{workflow_json}:The workflow JSON is valid.")
    else:
        print(f"{workflow_json}:Validation failed: {message}")
            
    data = osutil.get_wf_json(workflow_json)
    return data


# Function to check if enough time has elapsed since the last run
# if multi_instance return true=0
# else if job is running return ID of job
# else return true=0
def can_start_new_run(conn, workflow_name, schedule_interval, multi_instance):
    if multi_instance=='yes':
        return True
    #multi_instance='no'
        
    last_run = get_last_workflow_run(conn, workflow_name)
    if not last_run:
        return True
    elapsed_time = datetime.now() - last_run
    required_delay = timedelta(minutes=int(schedule_interval.split()[0]))
    return elapsed_time >= required_delay


async def execute_task(conn, task, workflow_run_id, workflow_name):
    task_name = task['name']
    task_type = task['type']
    callable_path = task['callable']
    args = task['args']
    is_sync = task.get('sync', True)

    try:
        # Add task to workflow_tasks with running state
        new_wf_task_id = add_workflow_task(conn, task_name, workflow_run_id, task['type'], 'running', datetime.now(), None)

        # Inject task_id into the args at the beginning
        args = {'wf_task_id': new_wf_task_id, **args}
        args = {'wf_run_id': workflow_run_id, **args}
        args = {'wf_name': workflow_name, **args}

        # Handle db_connection argument and ensure proper connection object
        db_connection = args.pop('db_connection', None)
        if db_connection:
            if conn.username == db_connection:
                args['db_connection'] = conn
            else:
                conn2 = myorcldb.get_otherdb_conn(db_connection)
                args['db_connection'] = conn2

        result = None

        if task_type == 'wf_standard':
            # Specific handling for wait_task
            if 'wait_task' in callable_path:
                seconds = args.get('seconds', 0)
                result = await wait_task(**args)
            else:
                # Determine the module and function to call for standard tasks
                module_path, function_name = callable_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                func = getattr(module, function_name)

                if asyncio.iscoroutinefunction(func):
                    result = await func(**args)
                else:
                    result = func(**args)

        elif task_type == 'PyNodeTask':
            # Handle custom Python tasks
            module_path, function_name = callable_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)

            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                if is_sync:
                    result = func(**args)
                else:
                    result = await asyncio.to_thread(func, **args)

        # Update task in workflow_tasks with finished state
        update_workflow_task(conn, new_wf_task_id, 'finished', result)

        # Update workflow states based on task
        if task_name == 'start_task':
            update_workflow_run(conn, workflow_run_id, 'running')
        elif task_name == 'end_task':
            update_workflow_run(conn, workflow_run_id, 'finished')

    except Exception as e:
        print(f"Unexpected error in task {task_name}: {e}")
        update_workflow_task(conn, new_wf_task_id, 'error', str(e))
        conn.rollback()

"""
async def execute_task_old(conn, task, workflow_run_id):
    task_name = task['name']
    task_type = task['type']
    callable_path = task['callable']
    args = task['args']
    is_sync = task.get('sync', True)
    conn2 = None
    try:
        # Add task to workflow_tasks with running state
        new_wf_task_id = add_workflow_task(conn, task_name, workflow_run_id, task['type'], 'running', datetime.now(), None)

        # Inject task_id into the args at the beginning
        args = {'wf_task_id': new_wf_task_id, **args}

        # Handle db_connection argument and ensure proper connection object
        db_connection = args.pop('db_connection', None)
        if db_connection:
            if conn.username == db_connection:
                args['db_connection'] = conn
            else:
                conn2 = myorcldb.get_otherdb_conn(db_connection)
                args['db_connection'] = conn2

        result = None

        # Determine the module and function to call
        try:
            module_path, function_name = callable_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            print(f"Error importing module or function: {e}")
            update_workflow_task(conn, new_wf_task_id, 'error', str(e))
            return

        # Check if the function is asynchronous
        try:
            if asyncio.iscoroutinefunction(func):
                # If the function is async, await it
                result = await func(**args)
            else:
                # If the function is sync, decide based on task's sync flag
                if is_sync:
                    result = func(**args)
                else:
                    result = await asyncio.to_thread(func, **args)
        except Exception as e:
            print(f"Error executing task {task_name}: {e}")
            update_workflow_task(conn, new_wf_task_id, 'error', str(e))
            return

        # Update task and workflow states
        if task_type == 'wf_standard' and task_name == 'start_task':
            update_workflow_run(conn, workflow_run_id, 'running')

        if task_type == 'wf_standard' and task_name == 'end_task':
            update_workflow_run(conn, workflow_run_id, 'finished')

        # Update task in workflow_tasks with finished state
        update_workflow_task(conn, new_wf_task_id, 'finished', result)

    except Exception as e:
        # General exception handler for any other unexpected errors
        print(f"Unexpected error in task {task_name}: {e}")
        update_workflow_task(conn, new_wf_task_id, 'error', str(e))
        conn.rollback()  # Rollback any partial changes
        if conn2:#local creation so release
                myorcldb.release_conn(conn2)

"""



#main function that interprets the wf file
async def main(workflow_json_file):
    wf_db_user =  os.getenv("WF_DB_USER")
    conn = None

    try:

        conn = myorcldb.get_otherdb_conn(wf_db_user) 
        #create wf tables if missing, self contained
        wf_util.check_and_create_wf_tables(conn)

        workflow = read_workflow_json(workflow_json_file)['workflow']
        workflow_name = workflow['name']
        schedule_interval = workflow['schedule_interval']
        multi_instance = workflow.get('multi_instance', 'no')

        if not can_start_new_run(conn, workflow_name, schedule_interval, multi_instance):
            print(f"{workflow_name}:Not enough time has elapsed since the last run.")
            return

        tasks = {task['name']: task for task in workflow['tasks']}
        completed_tasks = set()

        # Start the workflow run
        new_wf_id = add_workflow_run(conn, workflow_name, datetime.now(), 'new')

        # Execute tasks respecting the dependencies
        for dependency in workflow['dependencies']:
            upstream = dependency['upstream']
            downstream = dependency['downstream']

            if isinstance(upstream, str):
                upstream = [upstream]
            if isinstance(downstream, str):
                downstream = [downstream]

            # Wait for upstream tasks to complete
            for task_name in upstream:
                if task_name not in completed_tasks:
                    await execute_task(conn, tasks[task_name], new_wf_id,workflow_name)
                    completed_tasks.add(task_name)

            # Execute downstream tasks
            for task_name in downstream:
                if task_name not in completed_tasks:
                    await execute_task(conn, tasks[task_name], new_wf_id,workflow_name)
                    completed_tasks.add(task_name)

        # Update the workflow run to complete
        update_workflow_run(conn, new_wf_id, 'finished')

    except Exception as e:
        # Log the error and rollback any partial changes
        print(f"An error occurred during the execution of workflow {workflow_json_file}: {e}")
        if conn:
            conn.rollback()
        if 'new_wf_id' in locals():
            update_workflow_run(conn, new_wf_id, 'error')

    finally:
            # Ensure the database connection is released
            if conn:
                myorcldb.release_conn(conn)
