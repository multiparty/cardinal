class Handler:
    """
    Cloud provider API handler base class. Defines
    common API between inherited handler classes.
    """
    def __init__(self, app):
        self.app = app
        self.compute_client = None
        self.storage_client = None

    def fetch_available_ip_address(self):
        return ""

    """
    you'll need more methods, probably one for 
    each kubernetes object that you need to launch
    
    also -- i subclassed and pushed all this code into
    here so that every build() method in the compute_party
    class doesnt have like
    
    if my_provider == "AWS":
        # some boto3 code
    elif my_provider == "GCP":
        # some gcloud code
    etc.
    """