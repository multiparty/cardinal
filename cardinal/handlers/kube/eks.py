import boto3
import random
from cardinal.handlers.kube import KubeHandler


class EksHandler(KubeHandler):
    def __init__(self, app, region):
        super(EksHandler, self).__init__(app)
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=self.region)
        self.reserved_addresses = self.fetch_all_available_ip_addresses()

    def fetch_all_available_ip_addresses(self):
        response = self.ec2.describe_addresses()
        reserved = [item for item in response['Addresses'] if ('NetworkInterfaceId' not in item) and
                    (item['NetworkBorderGroup'] == self.region)]

        return reserved

    def fetch_available_ip_address(self):
        for_congregation = [ip['PublicIp'] for ip in self.reserved_addresses if self._valid_ip_address(ip, 'congregation')]

        if len(for_congregation) == 0:
            return ''

        return random.choice(for_congregation)

    def fetch_jiff_server_ip_address(self):
        for_jiff = [ip['PublicIp'] for ip in self.reserved_addresses if self._valid_ip_address(ip, 'jiff_server')]

        if len(self.reserved_addresses) == 0:
            return ''

        return random.choice(for_jiff)

    def _valid_ip_address(self, addr, use):
        if 'Tags' in addr:
            for tag in addr['Tags']:
                if tag['Key'] == 'use':
                    return tag['Value'] == use
        return False
