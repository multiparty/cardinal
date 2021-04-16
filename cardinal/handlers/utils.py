from cardinal.handlers import *


def resolve_handler(cloud_provider: str, app):

    if cloud_provider == "AWS":
        return AwsHandler(app)
    elif cloud_provider == "AZURE":
        return AzureHandler(app)
    elif cloud_provider == "GCP":
        return GcpHandler(app)
    else:
        app.logger.error(f"Unrecognized cloud provider: {cloud_provider}")