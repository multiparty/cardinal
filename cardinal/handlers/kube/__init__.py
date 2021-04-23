from cardinal.handlers.handler import Handler


class KubeHandler(Handler):
    """
    Handler for Kubernetes based cloud infrastructure (EKS, GKE, AKS)
    """
    def __init__(self, app):
        super(KubeHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""

    def launch_pod(self, spec: dict):
        pass

    def launch_service(self, spec: dict):
        pass
