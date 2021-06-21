import logging
import os
from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask import g
from flaskext.mysql import MySQL

from cardinal import Orchestrator

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
mysql = MySQL()


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

    infra = os.environ.get("CLOUD_PROVIDER")
    if infra in {"EC2", "EKS"}:
        msg = f"Unrecognized compute infrastructure: {infra}"
        app.logger.error(msg)
        raise Exception(msg)
    elif infra in {"GCE", "GKE"}:
        req = request.get_json(force=True)

        app.logger.info(f"Workflow submission received: {req}")
        app.config['MYSQL_DATABASE_USER'] = 'root'
        app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
        app.config['MYSQL_DATABASE_DB'] = 'Cardinal'
        app.config['MYSQL_DATABASE_HOST'] = req["db_ip"]

    elif infra in ("AKS", "AVM"):
        msg = f"Unrecognized compute infrastructure: {infra}"
        app.logger.error(msg)
        raise Exception(msg)

    mysql.init_app(app)

    conn = mysql.connect()
    conn.autocommit(True)
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS datasets( \
      datasetId           VARCHAR(150) NOT NULL,\
      endpoint            VARCHAR(150) NOT NULL,\
      PID                 INT unsigned NOT Null,\
      bigNumber           BOOL,\
      decimalDigits       INT unsigned,\
      integerDigits       INT unsigned,\
      negativeNumber      BOOL,\
      ZP                  BOOL,\
      PRIMARY KEY     (datasetId)\
    );")

    cursor.execute("CREATE TABLE IF NOT EXISTS pods \
                      datasetId           VARCHAR(150) NOT NULL,\
                      PID                 INT unsigned NOT NULL,\
                      ipAddr           VARCHAR(150) NOT NULL,\
                      PRIMARY KEY         (datasetId)\
                    );")

    cursor.execute("CREATE TABLE IF NOT EXISTS jiff_servers( \
                          datasetId           VARCHAR(150) NOT NULL,\
                          ipAddr           VARCHAR(150) NOT NULL,\
                          PRIMARY KEY         (datasetId)\
                        );")

    conn.close()

    return


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
        if req["workflow_name"] in get_running_jobs():
            orch = Orchestrator(req, app, len(get_running_jobs().keys()))
            conn = mysql.connect()
            conn.autocommit(True)
            cursor = conn.cursor()
            sql = "INSERT IGNORE INTO jiff_servers (datasetId, ipAddr ) VALUES ( %s, %s)"
            val = (req["workflow_name"], req['jiff_server'])
            cursor.execute(sql, val)
            conn.close()
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
        elif req["workflow_name"] in get_running_jobs():

            msg = f"Workflow with name {req['workflow_name']} already has a JIFF server."
            app.logger.error(msg)
            response = {
                "MSG": msg
            }
        # if they didn't start a JIFF server, start a new one and respond with its IP
        else:

            orch = Orchestrator(req, app, len(get_running_jobs().keys()))

            app.logger.info(f"Adding workflow with name {req['workflow_name']} to running jobs.")
            app.logger.info(f"Starting JIFF server for workflow: {req['workflow_name']}.")
            # Add entry to get_running_jobs() so that we can access that orchestrator later on
            # get_running_jobs()[req['workflow_name']] = orch

            jiff_ip = orch.start_jiff_server()

            conn = mysql.connect()
            conn.autocommit(True)
            cursor = conn.cursor()
            sql = "INSERT INTO jiff_servers (datasetId, ipAddr ) VALUES (%s, %s, %s)"
            val = (req["workflow_name"], req["from_pid"], f"{req['pod_ip_address']}:9000")
            cursor.execute(sql, val)
            conn.close()

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
        if req["workflow_name"] in get_running_jobs():
            """
            if this IP information is legitimate, fetch the corresponding 
            orchestrator and update its other_pod_ips record
            """

            app.logger.info(
                f"Received IP address from cardinal server generating pod "
                f"for party {req['from_pid']}"
            )
            # insert ips into database

            save_ip(req["workflow_name"], req["from_pid"], req['pod_ip_address'])

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
        if req["workflow_name"] in get_running_jobs():

            get_running_jobs()[req["workflow_name"]].stop_workflow()
            del get_running_jobs()[req["workflow_name"]]
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


def get_running_jobs():
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT datasetId FROM datasets WHERE running == 1")
    running_jobs = cursor.fetchmany()
    mysql.connect().close()
    app.logger.info(f"Running Jobs: {running_jobs}")
    return running_jobs


def get_ips(workflow_name):
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT * FROM pods WHERE datasetId == ?", workflow_name)
    ips = cursor.fetchmany()
    mysql.connect().close()
    app.logger.info(f"IPs: {ips}")
    return ips


def get_running_job(workflow_name):
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT datasetId FROM datasets WHERE datasetId == ? AND running == 1", workflow_name)
    running_jobs = cursor.fetchmany()
    app.logger.info(f"Running Jobs: {running_jobs}")
    mysql.connect().close()
    return running_jobs


def save_ip(workflow_name, from_pid, ip_addr):
    conn = mysql.connect()
    conn.autocommit(True)
    cursor = conn.cursor()
    sql = "INSERT IGNORE INTO pods (datasetId, PID, ipAddr ) VALUES (%s, %s, %s)"
    val = (workflow_name, from_pid, f"{ip_addr}:9000")
    cursor.execute(sql, val)
    conn.close()


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
