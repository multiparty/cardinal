from cardinal.handlers.gcp import GcpHandler


class GkeHandler(GcpHandler):
    def __init__(self, app):
        super(GkeHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
