from cardinal.handlers.aws import AwsHandler


class Ec2Handler(AwsHandler):
    def __init__(self, app):
        super(Ec2Handler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
