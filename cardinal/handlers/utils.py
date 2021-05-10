import os
from cardinal.handlers import *


def resolve_handler(infra: str, app):

    if infra == "EC2":
        return Ec2Handler(app)
    elif infra == "EKS":
        region = os.environ.get("REGION")
        return EksHandler(app, region)
    elif infra == "GCE":
        return GceHandler(app)
    elif infra == "GKE":
        project = os.environ.get("PROJECT")
        region = os.environ.get("REGION")
        return GkeHandler(app, project, region)
    elif infra == "AVM":
        return AvmHandler(app)
    elif infra == "AKS":
        sub_id = os.environ.get("SUB_ID")
        resource_group_name = os.environ.get("RESOURCE_GROUP_NAME")
        location = os.environ.get("LOCATION")
        return AksHandler(app, sub_id, resource_group_name, location)
    else:
        app.logger.error(f"Unrecognized compute infrastructure: {infra}")
