import random
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from cardinal.handlers.kube import KubeHandler


class GkeHandler(KubeHandler):
    def __init__(self, app, project, region):
        super(GkeHandler, self).__init__(app)
        self.credentials = GoogleCredentials.get_application_default()
        self.service = discovery.build('compute', 'v1', credentials=self.credentials)
        self.project = project
        self.region = region
        self.reserved_addresses = self.fetch_all_available_ip_addresses()

    def fetch_all_available_ip_addresses(self):
        request = self.service.addresses().list(project=self.project, region=self.region)
        reserved = []
        while request is not None:
            response = request.execute()

            reserved = [item for item in response['items'] if item['status'] == 'RESERVED' and
                        item['addressType'] == 'EXTERNAL']

            request = self.service.addresses().list_next(previous_request=request, previous_response=response)

        return reserved

    def fetch_available_ip_address(self):
        for_congregation = [ip['address'] for ip in self.reserved_addresses if ip['description'] == "congregation"]

        if len(for_congregation) == 0:
            return ''

        return random.choice(for_congregation)

    def fetch_jiff_server_ip_address(self):
        for_jiff = [ip['address'] for ip in self.reserved_addresses if ip['description'] == "jiff_server"]

        if len(self.reserved_addresses) == 0:
            return ''

        return random.choice(for_jiff)
