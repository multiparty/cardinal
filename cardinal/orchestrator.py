import os
from cardinal.compute_party import ComputeParty
from cardinal.handlers.utils import resolve_handler


class Orchestrator:
    def __init__(self, workflow_config: dict, app):
        self.workflow_config = workflow_config
        self.app = app
        self.compute_party = ComputeParty(workflow_config, app, self._resolve_handler())

    def _resolve_handler(self):
        return resolve_handler(os.environ.get("CLOUD_PROVIDER"), self.app)

    def run(self):
        """
        Assumptions:
            - chamberlain has already launched a jiff server for this computation,
            and it's running at the IP address from the workfow_config
            - the machines indicated by the "other_cardinals" entry are also
            generating compute_party pods for this computation
            - we are responsible for generating a compute_party pod which will
            run the specified workflow with PID = workflow_config["PID"]
        """

        self.compute_party.build_all()
        self.compute_party.launch_all()
