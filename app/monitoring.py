import os
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

PUSHGATEWAY_HOST = os.getenv("PUSHGATEWAY_HOST", "localhost:9091")

registry = CollectorRegistry()
workflow_status_gauge = Gauge(
    'workflow_run_status',
    'Status of workflow runs (1=finished, 0=error)',
    ['workflow_name'],
    registry=registry
)

def push_workflow_status(workflow_name: str, status: str):
    """Push workflow status to Prometheus Pushgateway.

    Parameters
    ----------
    workflow_name: str
        Name of the workflow.
    status: str
        Either 'finished' or 'error'. Other states are ignored.
    """
    value = 1 if status == 'finished' else 0
    workflow_status_gauge.labels(workflow_name=workflow_name).set(value)
    try:
        push_to_gateway(PUSHGATEWAY_HOST, job='workflow_engine', registry=registry)
    except Exception:
        # Avoid raising to keep workflow execution running
        pass
