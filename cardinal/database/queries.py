from cardinal.database import Workflow, Pod, Jiff_Server, app
from cardinal.database import db


def get_running_workflows():
    workflows = Workflow.query.all()
    app.logger.info(f"Workflows {workflows} ")
    return workflows


def get_ips(workflow_name):
    ips = Pod.query.filter(Pod.workflowName == workflow_name).all()
    app.logger.info(f"Ips {ips} ")
    return ips


def get_workflow(workflow_name):
    workflow = Workflow.query.filter(Workflow.workflowName == workflow_name).first()
    app.logger.info(f"Workflow {workflow} ")
    return workflow


def workflow_exists(workflow_name):
    workflow = Workflow.query.filter(Workflow.workflowName == workflow_name).first()
    app.logger.info(f"Workflow {workflow} ")
    return workflow is not None


def save_pod(workflow_name, from_pid, ip_addr):
    pod = Pod(workflow_name, from_pid, ip_addr)
    db.session.add(pod)
    db.session.commit()


def save_jiff_server(workflow_name, ip_addr):
    jiff_server = Jiff_Server(workflow_name, ip_addr)
    db.session.add(jiff_server)
    db.session.commit()


def delete_workflow(workflow):
    db.session.delete(workflow)
    db.session.commit()
