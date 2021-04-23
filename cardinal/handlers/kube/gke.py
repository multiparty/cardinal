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

    def fetch_available_ip_address(self):
        request = self.service.addresses().list(project=self.project, region=self.region)
        reserved = []
        while request is not None:
            response = request.execute()

            reserved = [item['address'] for item in response['items'] if item['status'] == 'RESERVED' and
                        item['addressType'] == 'EXTERNAL']

            request = self.service.addresses().list_next(previous_request=request, previous_response=response)

        if len(reserved) == 0:
            return ''

        return random.choice(reserved)
