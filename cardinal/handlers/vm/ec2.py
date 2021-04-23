from cardinal.handlers.vm import VmHandler


class Ec2Handler(VmHandler):
    def __init__(self, app):
        super(Ec2Handler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
