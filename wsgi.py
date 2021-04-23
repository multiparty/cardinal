import logging
import os
from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS

from cardinal import Orchestrator


RUNNING_JOBS = dict()


app = Flask(__name__)
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

        if req["workflow_name"] in RUNNING_JOBS:

            msg = f"Workflow with name {req['workflow_name']} is already running."
            app.logger.error(msg)
            response = {
                "MSG": msg
            }

            return jsonify(response)
        else:

            orch = Orchestrator(req, app)
            orch.run()

            app.logger.info(f"Adding workflow with name {req['workflow_name']} to running jobs.")
            # Add entry to RUNNING_JOBS so that we can access that orchestrator later on
            RUNNING_JOBS[req['workflow_name']] = orch

        response = {
            "ID": req["workflow_name"]
        }

        return jsonify(response)


@app.route("/api/submit_ip_address", methods=["POST"])
def submit_ip_address():
    """
    cardinal instances will use this endpoint to transmit the IP address
    that they have selected for the compute pod they intend to launch for
    a given workflow. once cardinal receives a message of this type, it
    fetches the orchestrator from it's RUNNING_JOBS record, and updates
    it's other_pod_ips record.
    """

    if request.method == "POST":
        """
        request could look like:
        {
            "workflow_name": "test-workflow",   # name of relevant workflow
            "from_pid": 2,                      # PID of pod that will be generated at source cardinal instance
            "pod_ip_address: "xx.xx.xx.xx"      # IP address of pod being generated at source cardinal instance
        }
        """

        req = request.get_json(force=True)
        if req["workflow_name"] in RUNNING_JOBS:
            """
            if this IP information is legitimate, fetch the corresponding 
            orchestrator and update its other_pod_ips record
            """

            app.logger.info(
                f"Received IP address from cardinal server generating pod "
                f"for party {req['from_pod']}"
            )
            orch = RUNNING_JOBS[req["workflow_name"]]
            orch.party.other_compute_ips[req["from_pod"]]["IP_PORT"] = \
                f"{req['pod_ip_address']}:{9000 + int(req['from_pod'])}"

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

        return response


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
        if req["workflow_name"] in RUNNING_JOBS:

            del RUNNING_JOBS[req["WORKFLOW_NAME"]]
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
