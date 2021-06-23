from cardinal.database.models import Workflow, Pod, Jiff_Server
from wsgi import db


def get_running_workflows():
    workflows = Workflow.query.all()
    return workflows


def get_ips(workflow_name):
    ips = Pod.query.filter(Pod.workflowName == workflow_name).all()
    return ips


def get_running_workflow(workflow_name):
    workflow = Workflow.query.filter(Workflow.workflowName == workflow_name).all()
    return workflow


def save_pod(workflow_name, from_pid, ip_addr):
    pod = Pod(workflow_name, from_pid, ip_addr)
    db.session.add(pod)
    db.session.commit()


def save_jiff_server(workflow_name, ip_addr):
    jiff_server = Jiff_Server(workflow_name, ip_addr)
    db.session.add(jiff_server)
    db.session.commit()
