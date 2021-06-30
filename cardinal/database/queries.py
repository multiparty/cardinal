from sqlalchemy import and_

from cardinal.database import Workflow, Pod, JiffServer, app, Dataset
from cardinal.database import db


def get_running_workflows():
    workflows = Workflow.query.all()
    db.session.commit()
    app.logger.info(f"Workflows {workflows} ")
    return workflows


def get_ips(workflow_name):
    ips = Pod.query.filter(Pod.workflow_name == workflow_name).all()
    db.session.commit()
    app.logger.info(f"Ips {ips} ")
    app.logger.info(f"Ips length: {len(ips)} ")
    return ips


def get_jiff_server_by_workflow(workflow_name):
    jiff_server = JiffServer.query.filter(JiffServer.workflow_name == workflow_name).first()
    db.session.commit()
    app.logger.info(f"Jiff Server {jiff_server} ")
    return jiff_server


def get_pod_by_workflow_and_pid(workflow_name, pid):
    pods = Pod.query.filter(and_(Pod.workflow_name == workflow_name, Pod.pid == pid)).all()
    db.session.commit()
    app.logger.info(f"Pods {pods} ")
    return pods


def get_workflow_by_operation_and_dataset_id(operation, dataset_id):
    workflow = Workflow.query.filter(and_(Workflow.operation == operation, Workflow.dataset_id == dataset_id)).first()
    db.session.commit()
    app.logger.info(f"Workflow {workflow} ")
    return workflow


def get_workflow_by_source_key(source_key):
    workflow = Workflow.query.filter(Workflow.source_key == source_key).first()
    db.session.commit()
    app.logger.info(f"Workflow {workflow} ")
    return workflow


def get_dataset_by_id_and_pid(dataset_id, pid):
    dataset = Dataset.query.filter(and_(Dataset.dataset_id == dataset_id, Dataset.pid == pid)).first()
    db.session.commit()
    app.logger.info(f"Dataset Server {dataset} ")
    return dataset


def workflow_exists(workflow_name):
    workflow = JiffServer.query.filter(JiffServer.workflow_name == workflow_name).first()
    db.session.commit()
    exists = workflow is not None
    app.logger.info(f"Workflow Exists: {exists} ")
    return exists


def dataset_exists(dataset_id, pid):
    dataset = Dataset.query.filter(and_(Dataset.dataset_id == dataset_id, Dataset.pid == pid)).first()
    db.session.commit()
    exists = dataset is not None

    app.logger.info(f"Dataset Exists: {exists} ")
    return exists


def save_dataset(dataset_id, source_bucket, source_key, pid):
    dataset = Dataset(dataset_id, source_bucket, source_key, pid)
    db.session.add(dataset)
    db.session.commit()


def save_pod(workflow_name, from_pid, ip_addr):
    pod = Pod(workflow_name, from_pid, ip_addr)
    db.session.add(pod)
    db.session.commit()


def save_workflow(source_key, source_bucket, operation, dataset_id,
                  big_number, fixed_point, decimal_digits, integer_digits, negative_number, zp):
    workflow = Workflow(source_key, source_bucket, operation, dataset_id,
                        big_number, fixed_point, decimal_digits, integer_digits, negative_number, zp)
    db.session.add(workflow)
    db.session.commit()


def save_jiff_server(workflow_name, ip_addr):
    jiff_server = JiffServer(workflow_name, ip_addr)
    db.session.add(jiff_server)
    db.session.commit()


def delete_entry(entry):
    db.session.delete(entry)
    db.session.commit()
