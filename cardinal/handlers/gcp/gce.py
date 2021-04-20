from cardinal.handlers.gcp import GcpHandler


class GceHandler(GcpHandler):
    def __init__(self, app):
        super(GceHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
