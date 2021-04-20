from cardinal.handlers.azure import AzureHandler


class AksHandler(AzureHandler):
    def __init__(self, app):
        super(AksHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
