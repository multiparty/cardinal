import json
import pystache
import os
import requests
import time

from cardinal.database.queries import save_pod, get_ips, workflow_exists
from cardinal.handlers.handler import Handler
# from wsgi import get_ips, get_running_workflow, save_pod

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
        self.this_compute_ip = self.fetch_available_ip_address()
        self.other_compute_ips = self._initialize_other_ips()

        # ports needed
        # query available ports
        # assigned by pid

        self.compute_node_port = 30001 + num_workflows
        self.jiff_node_port = 31000 + num_workflows
        self.running = True

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

    # def _check_ip_records(self):
    #     """
    #     Look at our record of other parties' compute pod IP addresses,
    #     return PIDs of any parties whose entries are still incomplete.
    #     """
    #
    #     incomplete = []
    #     for other_party in self.other_compute_ips.keys():
    #         if not self.other_compute_ips[other_party]["IP_PORT"]:
    #             incomplete.append(other_party)
    #
    #     return incomplete
    #
    # def _check_ip_record_acks(self):
    #
    #     un_acked = []
    #     for other_party in self.other_compute_ips.keys():
    #         if not self.other_compute_ips[other_party]["ACKED"]:
    #             un_acked.append(other_party)
    #
    #     return un_acked

    def _exchange_ips(self):
        """
        iterates over entries in self.other_pod_ips, and terminates only when we
        have both received all the other pod's IP addresses from the other cardinal
        servers and those cardinal servers have received ours
        """

        # Maybe and wait thread this off?
        # a way to kill this job?

        # all_ips_received = False
        # all_parties_acked = False

        #         req = {
        #             "workflow_name": self.workflow_config["workflow_name"],
        #             "from_pid": self.workflow_config["PID"],
        #             "pod_ip_address": self.this_compute_ip
        #         }

        save_pod(self.workflow_config["workflow_name"], self.workflow_config["PID"], self.this_compute_ip)
        ips = get_ips(self.workflow_config["workflow_name"])
        while self.running and workflow_exists(self.workflow_config["workflow_name"]) \
                and (len(ips) != len(self.workflow_config["other_cardinals"])):
            ips = get_ips(self.workflow_config["workflow_name"])
            #
            # for other_party in self.workflow_config["other_cardinals"]:
            #
            #     if not self.other_compute_ips[other_party[0]]["ACKED"]:
            #         # if we haven't received a message from this party indicating
            #         # that they've received our pod IP information, then we send
            #         # them that information
            #         req = {
            #             "workflow_name": self.workflow_config["workflow_name"],
            #             "from_pid": self.workflow_config["PID"],
            #             "pod_ip_address": self.this_compute_ip
            #         }
            #
            #         dest_server = other_party[1]
            #         resp = requests.post(f"{dest_server}/api/submit_ip_address", json=req).json()
            #         self.app.logger.info(f"Submitted IP address to {dest_server} and got response: \n{resp}")
            #
            #         if resp["MSG"] == "OK":
            #             self.other_compute_ips[other_party[0]]["ACKED"] = True
            #
            # incomplete_parties = self._check_ip_records()
            # incomplete_acks = self._check_ip_record_acks()
            #
            # if incomplete_parties:
            #     self.app.logger.info(f"Waiting for IP information from the following parties: {incomplete_parties}")
            # else:
            #     all_ips_received = True
            #
            # if incomplete_acks:
            #     self.app.logger.info(f"Waiting for IP acks from the following parties: {incomplete_acks}")
            # else:
            #     all_parties_acked = True

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
            1: xx.xx.xx.xx:9001,
            2: yy.yy.yy.yy:9002,
            3: zz.zz.zz.zz:9003
        }

        And produces:
        ["1:xx.xx.xx.xx:9001", "2:yy.yy.yy.yy:9002", "3:zz.zz.zz.zz:9003"]

        Which is just the format that the congregation config file uses for IP addresses
        of the other compute parties.
        """

        party_config = get_ips(self.workflow_config["workflow_name"])
        self.app.logger.info(f"Party Config: {party_config}")

        # return json.dumps([f"{k}:{self.other_compute_ips[k]['IP_PORT']}" for k in self.other_compute_ips.keys()])
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
        data = {
            "WORKFLOW_NAME": self.workflow_config["workflow_name"],
            "PID": int(self.workflow_config["PID"]),
            "ALL_PIDS": self._build_all_pids_list(),
            "USE_FLOATS": "false",  # TODO - will eventually be configurable, hardcoded fine for now
            "PARTIES_CONFIG": self._build_parties_config(),
            "JIFF_SERVER_IP": self.workflow_config["jiff_server"].split(":")[0],
            "JIFF_SERVER_PORT": int(self.workflow_config["jiff_server"].split(":")[1]),
            "ZP": 16777729,  # TODO - will eventually be configurable, hardcoded fine for now
            "FP_USE": "false",  # TODO - will eventually be configurable, hardcoded fine for now
            "FP_DECIMAL": 1,  # TODO - will eventually be configurable, hardcoded fine for now
            "FP_INTEGER": 1,  # TODO - will eventually be configurable, hardcoded fine for now
            "NN_USE": "false",  # TODO - will eventually be configurable, hardcoded fine for now
            "BN_USE": "false"  # TODO - will eventually be configurable, hardcoded fine for now
        }

        rendered = pystache.render(template, data)
        self.specs["CONGREGATION_CONFIG"] = rendered

    def fetch_available_ip_address(self):
        return self.handler.fetch_available_ip_address()

    def stop_workflow(self):
        """
        Overridden in subclasses
        """
        pass
