from app.wf.wf_util import get_workflow_task_result

def do_something(wf_task_id,wf_run_id,wf_name,branch_arg1, branch_arg2):
    print(f"{wf_name}:{wf_run_id}:Doing something with{wf_task_id} {branch_arg1}, {branch_arg2}")
    result = f"Processed{wf_task_id}  {branch_arg1}, {branch_arg2}"
    return result

def do_something_else(wf_task_id,wf_run_id,wf_name,db_connection,result_of_task_name, branch_arg2):
    print(f"{wf_name}:{wf_run_id}:Doing something else with{wf_task_id} {result_of_task_name}, {branch_arg2}")
    prior_task = get_workflow_task_result(db_connection, wf_task_id, result_of_task_name)
    result = f"Processed{wf_task_id}  {result_of_task_name}:{prior_task}, {branch_arg2}"
    return result
