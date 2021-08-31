from cardinal.party import Party
from cardinal.handlers.vm import VmHandler


"""
TODO:
    Need to launch a machine with:
        * SSH access
        * Ports 9000-(9000 + len(compute_parties)) open for whitelisted IP's (from self.other_compute_ips)
        * Probably from an AMI with docker preinstalled
        * Start docker daemon, run container
    Open issues:
        * Need to get congregation config on the actual machine and mounted to the container before it
        gets run. Probably just need to FTP the config file and protocol? I don't know of a way to attach
        a file to an instance before it is started.
"""


class VmParty(Party):
    def __init__(self, workflow_config: dict, app, handler: VmHandler, num_workflows: int):
        super(VmParty, self).__init__(workflow_config, app, handler, num_workflows)

    def run(self):
        self._exchange_ips()

