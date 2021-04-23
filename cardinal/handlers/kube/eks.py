from cardinal.handlers.kube import KubeHandler


class EksHandler(KubeHandler):
    def __init__(self, app):
        super(EksHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
