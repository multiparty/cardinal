import boto3
import random
from cardinal.handlers.kube import KubeHandler


class EksHandler(KubeHandler):
    def __init__(self, app, region):
        super(EksHandler, self).__init__(app)
        self.ec2 = boto3.client('ec2')
        self.region = region

    def fetch_available_ip_address(self):
        response = self.ec2.describe_addresses()
        reserved = [item for item in response['Addresses'] if ('NetworkInterfaceId' not in item) and
                    (item['NetworkBorderGroup'] == self.region)]
        if len(reserved) == 0:
            return ''

        return random.choice(reserved)
