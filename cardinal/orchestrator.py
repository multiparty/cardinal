import os
from cardinal.handlers.utils import resolve_handler
from cardinal.party.kube_party import KubeParty
from cardinal.party.vm_party import VmParty


class Orchestrator:
    def __init__(self, workflow_config: dict, app, num_workflows: int):
        self.workflow_config = workflow_config
        self.app = app
        self.num_workflows = num_workflows
        self.handler = self._resolve_handler()
        self.party = self._resolve_party()

    def _resolve_party(self):

        infra = os.environ.get("CLOUD_PROVIDER")
        if infra in {"EC2", "GCE", "AVM"}:
            return VmParty(self.workflow_config, self.app, self.handler, self.num_workflows)
        elif infra in {"EKS", "GKE", "AKS"}:
            return KubeParty(self.workflow_config, self.app, self.handler, self.num_workflows)
        else:
            msg = f"Unrecognized compute infrastructure: {infra}"
            self.app.logger.error(msg)
            raise Exception(msg)

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

        self.party.run()

    def start_jiff_server(self):
        jiff_ip = self.party.start_jiff_server()
        return jiff_ip

    def stop_workflow(self):
        self.party.stop_workflow()

    def update_jiff_server(self, jiff_server):
        self.party.workflow_config['jiff_server'] = jiff_server
