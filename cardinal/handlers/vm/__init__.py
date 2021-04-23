from cardinal.handlers.handler import Handler


class VmHandler(Handler):
    """
    Handler for VM based cloud infrastructure (EC2, GCE, AVM)
    """
    def __init__(self, app):
        super(VmHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""