from cardinal.handlers.vm import VmHandler


class AvmHandler(VmHandler):
    def __init__(self, app):
        super(AvmHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
