from cardinal.handlers.handler import Handler


class AwsHandler(Handler):
    """
    function handlers for aws, can use boto3
    https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
    """
    def __init__(self, app):
        super(AwsHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""

