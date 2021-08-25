import json
import pystache
import os
import requests
import time

from cardinal.database.queries import save_pod, get_ips, workflow_exists, get_workflow_by_operation_and_dataset_id, update_pod_event_timestamp
from cardinal.handlers.handler import Handler
import datetime
from cardinal.handlers.handler import Handler

"""
TODO: 
    - method to grab dataset metadata JSON from S3 for congregation config
"""


class Party:
    def __init__(self, workflow_config: dict, app, handler: Handler, num_workflows: int):
        self.workflow_config = workflow_config
        self.app = app
        self.handler = handler
        self.templates_directory = f"{os.path.dirname(os.path.realpath(__file__))}/templates"
        self.specs = {}
        self.this_compute_ip = ""
        self.other_compute_ips = self._initialize_other_ips()
        self.running = True
        self.event_timestamps = [] # list of dicts of format { 'PID' : ... , 'event' : "...." , 'time': ...}
        if os.environ.get('PROFILE') and os.environ.get('PROFILE').lower() == 'true':
            self.PROFILE = True
            self.pod_succeeded = False
        else:
            self.PROFILE = False

    def run(self):
        """
        Overridden in subclasses
        """
        pass

    def _initialize_other_ips(self):
        # """
        # we want a dictionary where each entry is like PID: <IP>:<PORT>, with a unique port for each
        # compute party. The way I'm doing a unique port is just 9000 + PID, so like 9001, 9002, etc.
        #
        # I'm setting the ip:port entries for each other compute party to None, because we haven't
        # actually exchanged IP addresses yet.
        # """

        # self entry

        ret = {
            int(self.workflow_config["PID"]): {
                "IP_PORT": "0.0.0.0:9000",
                "ACKED": True
            }
        }

        # entries for other compute parties
        for party in self.workflow_config["other_cardinals"]:
            ret[int(party[0])] = {
                "IP_PORT": None,
                "ACKED": False
            }

        return ret

    def _exchange_ips(self):
        """
        Assumes we have 3 parties to a computation.
        Submits its compute ip to the database
        Waits for other to submit theirs and proceeds when all are found.
        """

        # TODO should add better error checking and not assume 3 ip entries == 3 other cardinals
        save_pod(self.workflow_config["workflow_name"], self.workflow_config["PID"], self.this_compute_ip)
        ips = get_ips(self.workflow_config["workflow_name"])
        while self.running and workflow_exists(self.workflow_config["workflow_name"]) \
                and (len(ips) < 3):
            ips = get_ips(self.workflow_config["workflow_name"])

            # TODO store into compute ips
            time.sleep(3)

    def _build_all_pids_list(self):

        ret = [int(self.workflow_config["PID"])]
        for party in self.workflow_config["other_cardinals"]:
            ret.append(party[0])

        return sorted(ret)

    def _build_parties_config(self):
        """
        We call this method only after we've successfully run the self._exchange_ips()
        method, since it's input depend on that method's outputs.

        This function takes something like the following:
        {
            1: xx.xx.xx.xx:9000,
            2: yy.yy.yy.yy:9000,
            3: zz.zz.zz.zz:9000
        }

        And produces:
        ["1:xx.xx.xx.xx:9000", "2:yy.yy.yy.yy:9000", "3:zz.zz.zz.zz:9000"]

        Which is just the format that the congregation config file uses for IP addresses
        of the other compute parties.
        """

        ips = get_ips(self.workflow_config["workflow_name"])
        party_config = json.dumps([f"{k.pid}:{k.ip_addr}:9000" if k.pid != self.workflow_config["PID"] else f"{k.pid}:0.0.0.0:9000" for k in ips])
        self.app.logger.info(f"Party Config: {party_config}")
        return party_config

    def build_congregation_config(self):
        """
        Use pystache to build config from template files and data from workflow
        request, this flow can be used for building other specs.

        The parameters that will eventually be configurable will all have to do
        with the contents of the dataset. They're all jiff-specific and just have
        to do with what extensions/parameters were used to create the shares of
        the data.

        I think we can fetch this metadata using
        some kind of standard for how datasets are uploaded, like:

            - Say we have dataset input.csv on some s3 bucket called datasets.
            - we would then just ensure that when this dataset is uploaded at
            s3://datasets/input.csv, there's some other JSON file uploaded
            alongside it called input.json, that looks something like the following:

            {
                "use_floats": <bool>,
                "zp": <int>,
                "floating_point_use": <bool>,
                "floating_point_decimal": <int>,
                "floating_point_integer": <int>,
                "negative_number_use": <bool>,
                "bignumber_use": <bool>
            }

        And since we have the dataset ID from workflow_config, we can do a lookup
        for where that dataset is (lookup table OK to hardcode here for now), and
        then just grab a file from that location with a .json extension instead of
        .csv, since we ensure it exists when we upload the dataset.
        """

        template = open(f"{self.templates_directory}/congregation/congregation_config.tmpl").read()
        self.app.logger.info(f"WORKFLOW INFO: {self.workflow_config}")
        data = {
            "WORKFLOW_NAME": self.workflow_config["workflow_name"],
            "PID": int(self.workflow_config["PID"]),
            "ALL_PIDS": self._build_all_pids_list(),
            "USE_FLOATS": str(self.workflow_config["fixedPoint"]).lower(),
            "PARTIES_CONFIG": self._build_parties_config(),
            "JIFF_SERVER_IP": self.workflow_config["jiff_server"].split(":")[0],
            "JIFF_SERVER_PORT": int(self.workflow_config["jiff_server"].split(":")[1]),
            "ZP": self.workflow_config["zp"],
            "FP_USE": str(self.workflow_config["fixedPoint"]).lower(),
            "FP_DECIMAL": self.workflow_config["decimalDigits"],
            "FP_INTEGER": self.workflow_config["integerDigits"],
            "NN_USE": str(self.workflow_config["negativeNumber"]).lower(),
            "BN_USE": str(self.workflow_config["bigNumber"]).lower()
        }
        self.app.logger.info(f"Data {data}")

        rendered = pystache.render(template, data)
        self.specs["CONGREGATION_CONFIG"] = rendered
        self.app.logger.info(f"Data Rendered {rendered}")

    def fetch_available_ip_address(self):
        return self.handler.fetch_available_ip_address()

    def stop_workflow(self):
        """
        Overridden in subclasses
        """
        pass

    def send_pod_stats(self, pod_stats):
        endpoint = f'{os.environ.get("CHAMBERLAIN")}/api/running-jobs'
        payload = {
            'workflow_name': self.workflow_config['workflow_name'],
            'cpu_usage': pod_stats['cpu']['avg'],
            'memory_usage': pod_stats['memory']['avg']
        }
        try:
            self.app.logger.info("Sending pod stats to {} with payload: \n{}\n".format(endpoint, payload))
            requests.put(endpoint, json=payload)
        except Exception as e:
            self.app.logger.error("Error sending pod stats: \n{}\n".format(e))

    def add_event_dict(self, event_dict):
        """
        function to add an event to the event timestamps list
        params:
            event_dict: dict of format
            {
                'PID' : ... ,
                'event' : "...." ,
                'time': ... # datetime.datetime.now()
            }
        """
        update_pod_event_timestamp(self.workflow_config['workflow_name'],
                                        event_dict['PID'],
                                        event_dict['event'],
                                        event_dict['time'])
