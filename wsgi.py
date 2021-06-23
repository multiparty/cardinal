import logging
import os

from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://://root:password@10.100.0.3:3306/Cardinal'
db = SQLAlchemy(app)

db.create_all()
db.session.commit()

from cardinal.database.queries import get_running_workflows, save_pod, save_jiff_server
from cardinal import Orchestrator


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
    """
    {
        db_ip = "127.0.0.1"
    }
    """

    # infra = os.environ.get("CLOUD_PROVIDER")
    # if infra in {"EC2", "EKS"}:
    #     msg = f"Unrecognized compute infrastructure: {infra}"
    #     app.logger.error(msg)
    #     raise Exception(msg)
    # elif infra in {"GCE", "GKE"}:
    #     req = request.get_json(force=True)
    #
    #     app.logger.info(f"Workflow submission received: {req}")
    #     # app.config['MYSQL_DATABASE_USER'] = 'root'
    #     # app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
    #     # app.config['MYSQL_DATABASE_DB'] = 'Cardinal'
    #     # app.config['MYSQL_DATABASE_HOST'] = req["db_ip"]
    #     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://://root:password@10.100.0.3:3306/Cardinal'
    #     db = SQLAlchemy(app)
    #
    # elif infra in ("AKS", "AVM"):
    #     msg = f"Unrecognized compute infrastructure: {infra}"
    #     app.logger.error(msg)
    #     raise Exception(msg)
    #
    # db.create_all()
    #
    # conn = mysql.connect()
    # conn.autocommit(True)
    # cursor = conn.cursor()


@app.route("/api/submit", methods=["POST"])
def submit():
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
        req = request.get_json(force=True)
        app.logger.info(f"Workflow submission received: {req}")

        # party 1 should already have an orchestrator since they started the JIFF server
        # if req['PID'] == 1:
        if req["workflow_name"] in get_running_workflows():
            orch = Orchestrator(req, app, len(get_running_workflows().keys()))
            save_jiff_server(req["workflow_name"], req['jiff_server'])

            orch.run()

            response = {
                "ID": req["workflow_name"]
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
    # # all other parties need to make a new orchestrator
    # else:
    #     if req["workflow_name"] in get_running_jobs():
    #         msg = f"Workflow with name {req['workflow_name']} is already running."
    #         app.logger.error(msg)
    #         response = {
    #             "MSG": msg
    #         }
    #
    #     else:
    #         orch = Orchestrator(req, app, len(get_running_jobs().keys()))
    #         app.logger.info(f"Adding workflow with name {req['workflow_name']} to running jobs.")
    #         # Add entry to get_running_jobs() so that we can access that orchestrator later on
    #         get_running_jobs()[req['workflow_name']] = orch
    #
    #         orch.run()
    #
    #         response = {
    #             "ID": req["workflow_name"]
    #         }

    return jsonify(response)


@app.route("/api/start_jiff_server", methods=["POST"])
def start_jiff_server():
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
        elif req["workflow_name"] in get_running_workflows():

            msg = f"Workflow with name {req['workflow_name']} already has a JIFF server."
            app.logger.error(msg)
            response = {
                "MSG": msg
            }
        # if they didn't start a JIFF server, start a new one and respond with its IP
        else:

            orch = Orchestrator(req, app, len(get_running_workflows().keys()))

            app.logger.info(f"Adding workflow with name {req['workflow_name']} to running jobs.")
            app.logger.info(f"Starting JIFF server for workflow: {req['workflow_name']}.")
            # Add entry to get_running_jobs() so that we can access that orchestrator later on
            # get_running_jobs()[req['workflow_name']] = orch

            jiff_ip = orch.start_jiff_server()

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
    a given workflow. once cardinal receives a message of this type, it
    fetches the orchestrator from it's get_running_jobs() record, and updates
    it's other_pod_ips record.
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
        if req["workflow_name"] in get_running_workflows():
            """
            if this IP information is legitimate, fetch the corresponding 
            orchestrator and update its other_pod_ips record
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
            if the workflow_name doesn't resolve to a running orchestrator,
            return an error message
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

        req = request.get_json(force=True)
        if req["workflow_name"] in get_running_workflows():

            get_running_workflows()[req["workflow_name"]].stop_workflow()
            del get_running_workflows()[req["workflow_name"]]
            app.logger.info(f"Workflow {req['workflow_name']} complete, removed from running jobs.")
            response = {
                "MSG": "OK"
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


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
