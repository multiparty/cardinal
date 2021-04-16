from cardinal.handlers.handler import Handler


class GcpHandler(Handler):
    """
    function handlers for gcp, can use gcloud sdk
    https://github.com/googleapis/google-cloud-python
    """
    def __init__(self, app):
        super(GcpHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""