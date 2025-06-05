from app.service import myorcldb
import asyncio
import glob
import os
from app.wf import wf_engine
from app.service import myorcldb
from zoneinfo import ZoneInfo
from datetime import datetime

# Define the path to the directory containing the JSON files
WF_JSON_DIR = 'app/data/wf/'

async def process_all_workflows():
    dt =datetime(2024,12,25,12, tzinfo=ZoneInfo("America/New_York"))
    utc_now =datetime.now(tz=ZoneInfo("UTC"))
    est_now = utc_now.astimezone(ZoneInfo("America/New_York"))
    print("Runtime in UTC:",utc_now)
    print("Runtime in EST:",est_now)

    # Use glob to find all JSON files in the specified directory
    json_files = glob.glob(os.path.join(WF_JSON_DIR, '*.json'))

    # Create a list to hold all the workflow tasks
    workflow_tasks = []

    # Loop through all JSON files and create a separate async task for each workflow
    for json_file in json_files:
        # Extract just the file name from the full path
        file_name = os.path.basename(json_file)
        print(f"Scheduling workflow file: {file_name}")
        # Schedule each workflow to run as an independent asyncio task
        workflow_task = asyncio.create_task(wf_engine.main(file_name))
        workflow_tasks.append(workflow_task)

    # Wait for all workflow tasks to complete
    await asyncio.gather(*workflow_tasks)

if __name__ == "__main__":
    asyncio.run(process_all_workflows())
    myorcldb.close_pools()

