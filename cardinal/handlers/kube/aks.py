import random
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from cardinal.handlers.kube import KubeHandler


class AksHandler(KubeHandler):
    def __init__(self, app, sub_id, resource_group_name):
        super(AksHandler, self).__init__(app)
        self.credentials = DefaultAzureCredential()
        self.sub_id = sub_id
        self.resource_group_name = resource_group_name

    def fetch_available_ip_address(self):
        network_client = NetworkManagementClient(self.credentials, self.sub_id)
        results = network_client.public_ip_addresses.list(self.resource_group_name)
        reserved = [item.ip_address for item in results if not item.ip_configuration]

        return random.choice(reserved)
