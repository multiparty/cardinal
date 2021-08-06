import logging
import os
import time
from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from cardinal.database import app
from cardinal.database.queries import get_running_workflows, save_pod, save_jiff_server, workflow_exists, \
    save_workflow, delete_entry, get_jiff_server_by_workflow, dataset_exists, save_dataset, \
    get_pod_by_workflow_and_pid, get_workflow_by_source_key, get_dataset_by_id_and_pid, save_pod_event_timestamp, get_pod_event_timestamp_by_workflow_and_pid
from cardinal import Orchestrator

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return "homepage"


@app.route("/")
@app.route("/index")
def index():
    """
    homepage
    """
    return "homepage"


@app.route("/api/setup_db_conn", methods=["POST"])
def setup_db_conn():
    # TODO update so DB does not have to be hard coded
    # Currently DB is hardcoded
    """
    {
        db_ip = "127.0.0.1"
    }
    """


@app.route("/api/submit", methods=["POST"])
def submit():
    if request.method == "POST":
        """
        request looks like:
        {
            "workflow_name": computation_settings['workflow_name'],
            "dataset_id": computation_settings['dataset_id'],
            "operation": computation_settings['operation'],
            "cardinal_ip": IP,
            "workflow_source_bucket": computation_settings['workflow_source_bucket'],
            "workflow_source_key": computation_settings['workflow_source_key'],
            "PID": PID,
            "other_cardinals": [x for x in cardinals if not x == (PID, IP)],
            "jiff_server": jiff_server_IP,
            "bigNumber": False, 
            "negativeNumber":False, 
            "fixedPoint":False, 
            "integerDigits":0, 
            "decimalDigits": 0, 
            "ZP": 16777729
        }
        """
        req = request.get_json(force=True)
        app.logger.info(f"Workflow submission received: {req}")

        # party 1 should already have an orchestrator since they started the JIFF server
        # if req['PID'] == 1:
        if workflow_exists(req["workflow_name"]):
            orch = Orchestrator(req, app, len(get_running_workflows()))

            # save in pod event time stamp for party 2 and 3
            if req['PID'] != 1:
                save_pod_event_timestamp(req['workflow_name'],req['PID'])

            orch.run()

            response = {
                "ID": req["workflow_name"],
                "DESTINATION": f's3://{os.getenv("DESTINATION_BUCKET")}/{req["workflow_name"]}.csv'
            }

        else:
            app.logger.error(
                f"Receive workflow submission from chamberlain server "
                f"for workflow {req['workflow_name']}, but this workflow "
                f"isn't present in record of running workflows."
            )
            response = {
                "MSG": f"ERR: Workflow {req['workflow_name']} not present in record of running workflows."
            }

        return jsonify(response)


@app.route("/api/start_jiff_server", methods=["POST"])
def start_jiff_server():
    """
            request looks like:
            {
                "workflow_name": "test-workflow",
                "dataset_id": "HRI107",
                "operation": "std-dev",
                "PID": 1
                "other_cardinals": [(2, "23.45.67.89"), (3, "34.56.78.90")],
                "jiff_server": "45.67.89.01"
            }
    """
    if request.method == "POST":

        req = request.get_json(force=True)
        app.logger.info(f"JIFF server request received for workflow: {req['workflow_name']}")

        # only party 1 should start a JIFF server
        if req['PID'] != 1:
            msg = f"Party {req['PID']} cannot start a JIFF server. Send request to party 1."
            app.logger.error(msg)
            response = {
                "MSG": msg
            }
        # if it is party one, make sure they didn't already start a JIFF server
        elif workflow_exists(req["workflow_name"]):

            msg = f"Workflow with name {req['workflow_name']} already has a JIFF server."
            app.logger.error(msg)
            response = {
                "MSG": msg
            }
        # if they didn't start a JIFF server, start a new one and respond with its IP
        else:

            orch = Orchestrator(req, app, len(get_running_workflows()))

            app.logger.info(f"Adding workflow with name {req['workflow_name']} to running jobs.")
            app.logger.info(f"Starting JIFF server for workflow: {req['workflow_name']}.")

            # save in pod event time stamp for party 1
            save_pod_event_timestamp(req['workflow_name'],1)

            # TODO move this out so its not a hanging object
            jiff_ip = orch.start_jiff_server()

            # Save server to database for lookup later
            save_jiff_server(req["workflow_name"], jiff_ip)

            response = {
                "JIFF_SERVER_IP": jiff_ip + ":8080"
            }

        return jsonify(response)


@app.route("/api/submit_ip_address", methods=["POST"])
def submit_ip_address():
    """
    cardinal instances will use this endpoint to transmit the IP address
    that they have selected for the compute pod they intend to launch for
    a given workflow. .
    """

    if request.method == "POST":
        """
        request could look like:
        {
            "workflow_name": "test-workflow",   # name of relevant workflow
            "from_pid": 2,                      # PID of pod that will be generated at source cardinal instance
            "pod_ip_address": "xx.xx.xx.xx"      # IP address of pod being generated at source cardinal instance
        }
        """

        req = request.get_json(force=True)
        if workflow_exists(req["workflow_name"]):
            """
            if this IP information is legitimate, fetch the corresponding 
            orchestrator and save to the database
            """

            app.logger.info(
                f"Received IP address from cardinal server generating pod "
                f"for party {req['from_pid']}"
            )
            # insert ips into database

            save_pod(req["workflow_name"], req["from_pid"], req['pod_ip_address'])

            response = {
                "MSG": "OK"
            }
        else:
            """
            if the workflow_name does not exist in the database
            """

            app.logger.error(
                f"Receive IP address from cardinal server generating pod"
                f"for workflow {req['workflow_name']}, but this workflow "
                f"isn't present in record of running workflows."
            )
            response = {
                "MSG": f"ERR: Workflow {req['workflow_name']} not present in record of running workflows."
            }

        return jsonify(response)


@app.route("/api/submit_workflow", methods=["POST"])
def submit_workflow():
    # Submit a workflow to the database to be used later on a data set

    if request.method == "POST":
        """
        request could look like:
        {
            "source_key": "HRIO/workflow/std_dev_HRI0.py",   # name of relevant workflow
            "source_bucket": HRI0, 
            "operation": stv_dev, 
            "dataset_id": HRI0, 
            "big_number": true, 
            "fixed_point": true, 
            "decimal_digits": 2, 
            "integer_digits": 2,
            "negative_number": 2,
            "zp: : true
            
        }
        """

        req = request.get_json(force=True)
        if get_workflow_by_source_key(req["source_key"]) is not None:
            """
            Check if the workflow exists and do no insert if it is no unique
            """

            app.logger.error(
                f"Error saving workflow, workflow already exists. (Try running workflow complete) "
            )

            response = {
                "MSG": f"ERR: Workflow {req['source_key']} already exists."
            }
        else:

            app.logger.info(
                f"Saving workflow {req['source_key']}"
                f"for workflow {req['source_key']}, but this workflow "
                f"isn't present in record of running workflows."
            )

            save_workflow(req['source_key'], req['source_bucket'], req['operation'], req['dataset_id'],
                          req['big_number'], req['fixed_point'],
                          req['decimal_digits'], req['integer_digits'], req['negative_number'], req['zp'])
            response = {
                "MSG": "OK"
            }

        return jsonify(response)


@app.route("/api/submit_dataset", methods=["POST"])
def submit_dataset():
    """
   data = {
        datasetId = db.Column(db.String(150))
        sourceBucket = db.Column(db.String(150))
        sourceKey = db.Column(db.String(150))
        PID = db.Column(db.Integer)
        }
    """

    if request.method == "POST":
        """
        request could look like:
        {
            "dataset_id": "HRI0",   # name of relevant workflow
            "source_bucket": "HRI0",                   
            "source_key": "HRIO/workflow/std_dev_HRI0.py", 
            "pid": 2, 

        }
        """

        req = request.get_json(force=True)
        if dataset_exists(req["dataset_id"], req['PID']):

            app.logger.error(
                f"Error saving dataset, dataset already exists. (Try updating the dataset) "
                f"for party {req['PID']}"
            )

            response = {
                "MSG": f"ERR: Dataset {req['dataset_id']} already exists."
            }
        else:

            app.logger.info(
                f"Saving dataset {req['dataset_id']}"
            )

            save_dataset(req['dataset_id'], req['source_bucket'], req['source_key'], req['PID'])
            response = {
                "MSG": "OK"
            }

        return jsonify(response)


@app.route("/api/delete_dataset", methods=["POST"])
def delete_dataset():
    """
   data = {
        datasetId = db.Column(db.String(150))
        PID = db.Column(db.Integer)
        }
    """

    if request.method == "POST":
        """
        request could look like:
        {
            "dataset_id": "HRI0",   # name of relevant workflow
            "pid": 2, 

        }
        """

        req = request.get_json(force=True)
        dataset = get_dataset_by_id_and_pid(req["dataset_id"], req['PID'])
        if dataset is not None:

            delete_entry(dataset)
            app.logger.info(
                f"Deleted dataset {req['dataset_id']}for party {req['PID']}"
            )

            response = {
                "MSG": "OK"
            }
        else:

            app.logger.error(
                f"Error deleting dataset {req['dataset_id']}"
            )

            response = {
                "MSG": "Error deleting dataset"
            }

        return jsonify(response)


@app.route("/api/delete_workflow", methods=["POST"])
def delete_workflow():
    # Submit a workflow to the database to be used later on a data set

    if request.method == "POST":
        """
        request could look like:
        {
            "source_key": "HRIO/workflow/std_dev_HRI0.py",   # name of relevant workflow
        }
        """

        req = request.get_json(force=True)
        workflow = get_workflow_by_source_key(req["source_key"])
        if workflow is not None:
            """
            Check if the workflow exists and if so then delete
            """
            delete_entry(workflow)

            app.logger.info(
                f"Deleted workflow {req['source_key']}"
            )

            response = {
                "MSG": "OK"
            }

        else:

            app.logger.error(
                f"Error deleting workflow, workflow does not exist. "
            )

            response = {
                "MSG": f"ERR: Workflow {req['source_key']} does not exist."
            }

        return jsonify(response)


@app.route("/api/workflow_complete", methods=["POST"])
def workflow_complete():
    """
    Receives notification from congregation pods that its workflow has
    completed, and removes this workflow from record of running jobs.
    """

    if request.method == "POST":
        """
        request looks like:
        {
            "workflow_name": "test-workflow",
            "dataset_id": "HRI107",
            "operation": "std-dev",
            "PID": 1
            "other_cardinals": [(2, "23.45.67.89"), (3, "34.56.78.90")],
            "jiff_server": "45.67.89.01"
        }
        """

        # TODO ensure only targets its own running jobs
        req = request.get_json(force=True)

        pods = get_pod_by_workflow_and_pid(req["workflow_name"], req["PID"])
        if pods is not None:
            for pod in pods:
                delete_entry(pod)

            jiff_server = get_jiff_server_by_workflow(req["workflow_name"])
            if jiff_server is not None:
                delete_entry(jiff_server)

            orch = Orchestrator(req, app, len(get_running_workflows()))

            orch.stop_workflow()

            app.logger.info(f"Workflow {req['workflow_name']} complete, removed from running jobs.")

            event_timestamps = get_pod_event_timestamp_by_workflow_and_pid(req['workflow_name'],req['PID'])
            if event_timestamps is not None:
                delete_entry(event_timestamps)

            event_timestamps_dict = {x.name: str(getattr(event_timestamps, x.name)) for x in event_timestamps.__table__.columns}

            response = {
                "MSG": "OK",
                "timestamps": event_timestamps_dict
            }
        else:

            app.logger.error(
                f"Received request indicating the workflow {req['workflow_name']} "
                f"completed, but this workflow is not present in running jobs"
                f"record. Nothing to do.")
            response = {
                "MSG": f"ERR: {req['workflow_name']} not in running jobs record."
            }

        return jsonify(response)


@app.route("/api/status", methods=["POST"])
def get_status():
    # TODO tie this in with requests that can fetch the status of the pod from the cluster
    """
    Returns the status of the pod.
    """

    if request.method == "POST":
        """
        request looks like:
        {
            "workflow_name": "test-workflow"
        }
        """

        req = request.get_json(force=True)
        if workflow_exists(req['workflow_name']):
            # TODO fit into database
            # Get the pod by workflow and read the status
            # status = RUNNING_JOBS[req['workflow_name']].get_pod_status()
            status = ''
            response = {
                "status": status
            }
        else:
            app.logger.error(
                f"Received request asking the pod status in {req['workflow_name']} "
                f"but this workflow is not present in running jobs"
                f"record. Nothing to do.")
            response = {
                "MSG": f"ERR: {req['workflow_name']} not in running jobs record."
            }

        return jsonify(response)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
