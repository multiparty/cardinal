from cardinal.handlers.kube import KubeHandler


class AksHandler(KubeHandler):
    def __init__(self, app):
        super(AksHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
