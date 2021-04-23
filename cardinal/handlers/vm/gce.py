from cardinal.handlers.vm import VmHandler


class GceHandler(VmHandler):
    def __init__(self, app):
        super(GceHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
