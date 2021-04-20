from cardinal.handlers.aws import AwsHandler


class EksHandler(AwsHandler):
    def __init__(self, app):
        super(EksHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""

