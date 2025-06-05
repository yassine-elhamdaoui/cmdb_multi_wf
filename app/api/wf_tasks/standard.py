#Standard Functions
import asyncio

def start_workflow(wf_task_id,wf_run_id,wf_name):
    print(f"{wf_name}:{wf_run_id}:start workflow:{wf_task_id}")
    result = f"{wf_name}:{wf_run_id}:start workflow"
    return result 

def end_workflow(wf_task_id,wf_run_id,wf_name):
    print(f"{wf_name}:{wf_run_id}:End workflow:{wf_task_id}")
    result = f"{wf_name}:{wf_run_id}:End workflow"
    return result 

async def wait_task(wf_task_id,wf_run_id,wf_name,seconds):
    print(f"{wf_name}:{wf_run_id}:Waiting for:{seconds} seconds")
    await asyncio.sleep(seconds)
    print(f"{wf_name}:{wf_run_id}:Waiting for:{seconds} seconds")
    return (f"{wf_name}:{wf_run_id}:Waited for:{seconds} seconds") 