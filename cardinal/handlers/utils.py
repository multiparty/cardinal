import os
from cardinal.handlers import *


def resolve_handler(infra: str, app):

    if infra == "EC2":
        return Ec2Handler(app)
    elif infra == "EKS":
        return EksHandler(app)
    elif infra == "GCE":
        return GceHandler(app)
    elif infra == "GKE":
        project = os.environ.get("PROJECT")
        region = os.environ.get("REGION")
        return GkeHandler(app, project, region)
    elif infra == "AVM":
        return AvmHandler(app)
    elif infra == "AKS":
        return AksHandler(app)
    else:
        app.logger.error(f"Unrecognized compute infrastructure: {infra}")
