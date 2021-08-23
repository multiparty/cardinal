import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

load_dotenv()
app = Flask(__name__)
# TODO Example string change for your databases
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.environ.get("MYSQL_USER")}:{os.environ.get("MYSQL_PASSWORD")}' \
    f'@{os.environ.get("MYSQL_HOST")}:{os.environ.get("MYSQL_PORT")}/{os.environ.get("MYSQL_DB")}'
db = SQLAlchemy(app)

"""
SQLALchemy works by searching for classes with db.Model and turning them into tables.
The tables are automatically created if they do not exist but are not automatically updated if changed
"""
class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(150))
    source_bucket = db.Column(db.String(150))
    source_key = db.Column(db.String(150))
    pid = db.Column(db.Integer)

    def __init__(self, dataset_id, source_bucket, source_key, pid):
        self.datasetId = dataset_id
        self.sourceBucket = source_bucket
        self.sourceKey = source_key
        self.PID = pid

    def __repr__(self):
        return '<datasetId %r>' % self.dataset_id


class Workflow(db.Model):
    source_key = db.Column(db.String(150), primary_key=True)
    source_bucket = db.Column(db.String(150))
    operation = db.Column(db.String(150))
    dataset_id = db.Column(db.String(150))
    big_number = db.Column(db.Boolean)
    fixed_point = db.Column(db.Boolean)
    decimal_digits = db.Column(db.Integer)
    integer_digits = db.Column(db.Integer)
    negative_number = db.Column(db.Boolean)
    zp = db.Column(db.Integer)

    def __init__(self, source_key, source_bucket, dataset_id, operation, big_number,
                 fixed_point, decimal_digits, integer_digits, negative_number,
                 zp):
        self.source_key = source_key
        self.source_bucket = source_bucket
        self.dataset_id = dataset_id
        self.operation = operation
        self.big_number = big_number
        self.fixed_point = fixed_point
        self.decimal_digits = decimal_digits
        self.integer_digits = integer_digits
        self.negative_number = negative_number
        self.zp = zp

    def __repr__(self):
        return '<source_key %r>' % self.source_key


class Pod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(150))
    pid = db.Column(db.Integer)
    ip_addr = db.Column(db.String(150))

    def __init__(self, workflow_name, pid, ip_addr):
        self.workflow_name = workflow_name
        self.pid = pid
        self.ip_addr = ip_addr

    def __repr__(self):
        return '<Pod ip %r>' % self.ip_addr


class JiffServer(db.Model):
    workflow_name = db.Column(db.String(150), primary_key=True)
    ip_addr = db.Column(db.String(150))

    def __init__(self, workflow_name, ip_addr):
        self.workflow_name = workflow_name
        self.ip_addr = ip_addr

    def __repr__(self):
        return '<Jiff ip %r>' % self.ip_addr

class PodEventTimestamp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(150))
    pid = db.Column(db.Integer)
    jiff_server_launched = db.Column(db.Time)
    service_ip_retrieved = db.Column(db.Time)
    exchanged_ips = db.Column(db.Time)
    built_specs_configs = db.Column(db.Time)
    launched_config = db.Column(db.Time)
    launched_pod = db.Column(db.Time)
    pod_succeeded = db.Column(db.Time)
    workflow_stopped = db.Column(db.Time)

    def __init__(self, workflow_name, pid):
        self.workflow_name = workflow_name
        self.pid = pid

    def __repr__(self):
        return '<Pod id %r>' % self.pid

class PodResourceConsumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(1000))
    pid = db.Column(db.Integer)
    memory_usage = db.Column(db.Integer)
    cpu_usage = db.Column(db.Integer)
    timestamp = db.Column(db.Time)

    def __init__(self, workflow_name, pid,cpu,memory,timestamp):
        self.workflow_name = workflow_name
        self.pid = pid
        self.cpu_usage = cpu
        self.memory_usage = memory
        self.timestamp = timestamp

    def __repr__(self):
        return '<Pod id %r>' % self.pid

db.create_all()
db.session.commit()
