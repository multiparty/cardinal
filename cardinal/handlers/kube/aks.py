import random
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from cardinal.handlers.kube import KubeHandler


class AksHandler(KubeHandler):
    def __init__(self, app, sub_id, resource_group_name, location):
        super(AksHandler, self).__init__(app)
        self.credentials = DefaultAzureCredential()
        self.sub_id = sub_id
        self.resource_group_name = resource_group_name
        self.location = location
        self.reserved_addresses = self.fetch_all_available_ip_addresses()

    def fetch_all_available_ip_addresses(self):
        network_client = NetworkManagementClient(self.credentials, self.sub_id)
        results = network_client.public_ip_addresses.list(self.resource_group_name)
        reserved = [item for item in results if (item.location == self.location) and not item.ip_configuration]

        return reserved

    def fetch_available_ip_address(self):
        for_congregation = [ip.ip_address for ip in self.reserved_addresses if ip.tags['use'] == "congregation"]

        if len(for_congregation) == 0:
            return ''

        return random.choice(for_congregation)

    def fetch_jiff_server_ip_address(self):
        for_jiff = [ip.ip_address for ip in self.reserved_addresses if ip.tags['use'] == "jiff_server"]

        if len(self.reserved_addresses) == 0:
            return ''

        return random.choice(for_jiff)
