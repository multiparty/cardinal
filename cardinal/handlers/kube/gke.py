from cardinal.handlers.kube import KubeHandler


class GkeHandler(KubeHandler):
    def __init__(self, app):
        super(GkeHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""
