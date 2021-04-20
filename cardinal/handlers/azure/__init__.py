from cardinal.handlers.handler import Handler


class AzureHandler(Handler):
    """
    function handlers for azure, can use some azure python
    sdk (eg https://azure.github.io/azure-sdk-for-python/)
    """
    def __init__(self, app):
        super(AzureHandler, self).__init__(app)

    def fetch_available_ip_address(self):
        return ""