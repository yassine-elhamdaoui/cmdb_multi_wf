import json
from app.util import osutil

def validate_workflow_json(filename):
    expected_workflow_fields = {'name', 'description', 'schedule_interval', 'multi_instance', 'tasks', 'dependencies'}
    expected_task_fields = {'name', 'type', 'callable', 'args', 'sync'}
    expected_dependency_fields = {'upstream', 'downstream'}

    try:
        
        data = osutil.get_wf_json(filename)


        # Check for top-level 'workflow' key
        if 'workflow' not in data:
            return False, "'workflow' key is missing"

        workflow = data['workflow']

        # Check for unexpected fields in workflow
        unexpected_fields = workflow.keys() - expected_workflow_fields
        if unexpected_fields:
            return False, f"Unexpected fields in workflow: {unexpected_fields}"

        # Validate each task
        for task in workflow.get('tasks', []):
            unexpected_fields = task.keys() - expected_task_fields
            if unexpected_fields:
                return False, f"Unexpected fields in task '{task.get('id', 'unknown')}': {unexpected_fields}"

        # Validate dependencies
        for dependency in workflow.get('dependencies', []):
            unexpected_fields = dependency.keys() - expected_dependency_fields
            if unexpected_fields:
                return False, f"Unexpected fields in dependency: {unexpected_fields}"

        return True, "Validation successful"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"An error occurred: {e}"

