from sqlalchemy import and_

from cardinal.database import Workflow, Pod, JiffServer, app, Dataset
from cardinal.database import db


def get_running_workflows():
    workflows = Workflow.query.all()
    app.logger.info(f"Workflows {workflows} ")
    return workflows


def get_ips(workflow_name):
    ips = Pod.query.filter(Pod.workflowName == workflow_name).all()
    app.logger.info(f"Ips {ips} ")
    app.logger.info(f"Ips length: {len(ips)} ")
    return ips


def get_jiff_server_by_workflow(workflow_name):
    jiff_server = JiffServer.query.filter(JiffServer.workflowName == workflow_name).first()
    app.logger.info(f"Jiff Server {jiff_server} ")
    return jiff_server


def get_pod_by_workflow_and_pid(workflow_name, pid):
    pods = Pod.query.filter(and_(Pod.workflowName == workflow_name, Pod.PID == pid)).first()
    app.logger.info(f"Pods {pods} ")
    return pods


def get_workflow_by_name(workflow_name):
    workflow = Workflow.query.filter(Workflow.workflowName == workflow_name).first()
    app.logger.info(f"Workflow {workflow} ")
    return workflow


def get_dataset_by_id_and_pid(dataset_id, pid):
    dataset = Dataset.query.filter(and_(Dataset.datasetId == dataset_id, Dataset.PID == pid)).first()
    app.logger.info(f"Dataset Server {dataset} ")
    return dataset


def workflow_exists(workflow_name):
    workflow = JiffServer.query.filter(JiffServer.workflowName == workflow_name).first()
    exists = workflow is not None
    app.logger.info(f"Workflow Exists: {exists} ")
    return exists


def dataset_exists(dataset_id, pid):
    dataset = Dataset.query.filter(and_(Dataset.datasetId == dataset_id, Dataset.PID == pid)).first()
    exists = dataset is not None

    app.logger.info(f"Dataset Exists: {exists} ")
    return exists


def save_dataset(dataset_id, source_bucket, source_key, PID):
    dataset = Dataset(dataset_id, source_bucket, source_key, PID)
    db.session.add(dataset)
    db.session.commit()


def save_pod(workflow_name, from_pid, ip_addr):
    pod = Pod(workflow_name, from_pid, ip_addr)
    db.session.add(pod)
    db.session.commit()


def save_workflow(workflow_name, bigNumber, fixedPoint, decimalDigits, integerDigits, negativeNumber, ZP):
    workflow = Workflow(workflow_name, bigNumber, fixedPoint, decimalDigits, integerDigits, negativeNumber, ZP)
    db.session.add(workflow)
    db.session.commit()


def save_jiff_server(workflow_name, ip_addr):
    jiff_server = JiffServer(workflow_name, ip_addr)
    db.session.add(jiff_server)
    db.session.commit()


def delete_entry(entry):
    db.session.delete(entry)
    db.session.commit()
