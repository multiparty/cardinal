import base64
import json
import os
import pystache
import time
import yaml
from cardinal.party import Party
from cardinal.handlers.kube import KubeHandler
from kubernetes import client as k_client
from kubernetes import config as k_config
from kubernetes.client.rest import ApiException


class KubeParty(Party):
    def __init__(self, workflow_config: dict, app, handler: KubeHandler, num_workflows: int):
        super(KubeParty, self).__init__(workflow_config, app, handler, num_workflows)
        self.spec_prefix = f"{self.workflow_config['workflow_name'].lower()}-{self.workflow_config['dataset_id'].lower()}-{self.workflow_config['PID']}"
        # k_config.load_kube_config() # for local dev
        k_config.load_incluster_config()
        self.kube_client = k_client.CoreV1Api()

    def run(self):
        self.prepare_all()
        self.launch_all()

    def start_jiff_server(self):
        pod, service = self.build_jiff_specs()
        self.launch_service(service)
        jiff_ip = ""
        try:
            jiff_ip = self._get_service_ip(f"{self.spec_prefix}-jiff-server-service")
        except Exception as e:
            self.app.logger.error("Failed to get JIFF IP address: \n{}\n".format(e))

        self.launch_pod(pod)
        return jiff_ip

    def build_jiff_specs(self):
        pod_params = {
            "POD_NAME": f"{self.spec_prefix}-jiff-server",
            "JOB_ID": self.spec_prefix,
        }
        pod_template = open(f"{self.templates_directory}/kube/jiff_pod.tmpl", 'r').read()
        pod_rendered = pystache.render(pod_template, pod_params)

        service_params = {
            "POD_NAME": f"{self.spec_prefix}-jiff-server",
            "SERVICE_NAME": f"{self.spec_prefix}-jiff-server-service",
            "SERVICE_PORT": 8080,
        }
        service_template = open(f"{self.templates_directory}/kube/service.tmpl", 'r').read()
        service_rendered = pystache.render(service_template, service_params)

        return yaml.safe_load(pod_rendered), yaml.safe_load(service_rendered)

    def build_pod_spec(self):
        params = {
            "POD_NAME": f"{self.spec_prefix}-pod",
            "CONG_IMG_PATH": "docker.io/hicsail/congregation-jiff:latest",
            "INFRA": "AWS",
            "STORAGE_HANDLER_CONFIG": "/data/curia_config.txt",
            "SOURCE_BUCKET": os.environ.get("SOURCE_BUCKET"),
            "SOURCE_KEY": os.environ.get("SOURCE_KEY"),
            "WRITE_PATH": "/data/inpt.csv",
            "DESTINATION_BUCKET": os.environ.get("DESTINATION_BUCKET"),
            "CONFIGMAP_NAME": f"{self.spec_prefix}-config-map",
        }
        data_template = open(f"{self.templates_directory}/kube/pod.tmpl", 'r').read()

        rendered = pystache.render(data_template, params)
        self.specs["POD"] = rendered

    def build_service_spec(self):
        params = {
            "POD_NAME": f"{self.spec_prefix}-pod",
            "SERVICE_NAME": f"{self.spec_prefix}-service",
            "SERVICE_PORT": 9000,
        }
        data_template = open(f"{self.templates_directory}/kube/service.tmpl", 'r').read()

        rendered = pystache.render(data_template, params)
        self.specs["SERVICE"] = rendered

    def build_config_map(self):
        """
        The config map will have:
            - the congregation workflow to be run
            - the congregation config that gets generated by build_congregation_config()
            - the cloud storage endpoint for the input dataset (eg s3://datasets/input.csv)
                * we assume that the generated pod has environment variables injected into
                when we define the pod which allow it to authenticate against the cloud storage.
                These environment variables are also present on this machine (since we're making
                API calls to aws/gcloud/azure), so we can just grab them from the environment.
        """
        encoded_config = base64.b64encode(bytes(self.specs['CONGREGATION_CONFIG'], 'utf-8'))
        # TODO: fill in the "FILL IN" values in creds dict with your credentials
        aws_creds = {'AWS_REGION': os.environ.get("AWS_REGION"), 'AWS_ACCESS_KEY_ID': os.environ.get("AWS_ACCESS_KEY_ID"),
                     'AWS_SECRET_ACCESS_KEY': os.environ.get("AWS_SECRET_ACCESS_KEY")}
        encoded_creds = base64.b64encode(bytes(json.dumps(aws_creds), 'utf-8'))

        protocol_tmpl = open(f"{self.templates_directory}/congregation/protocol.tmpl", 'r').read()
        encoded_protocol = base64.b64encode(bytes(pystache.render(protocol_tmpl, {}), 'utf-8'))
        params = {
            "POD_NAME": f"{self.spec_prefix}-pod",
            "CONFIGMAP_NAME": f"{self.spec_prefix}-config-map",
            "WORKFLOW_NAME": self.workflow_config['workflow_name'],
            "PROTOCOL": encoded_protocol,
            "CONG_CONFIG": encoded_config,
            "CURIA_CONFIG": encoded_creds
        }
        data_template = open(f"{self.templates_directory}/kube/config_map.tmpl", 'r').read()

        rendered = pystache.render(data_template, params)
        self.specs["CONFIG_MAP"] = rendered

    def _get_service_ip(self, service_name):
        ip_address = ""
        start_time = time.time()
        elapsed_time = 0
        infra = os.environ.get("CLOUD_PROVIDER")

        while not ip_address and elapsed_time < 180:
            time.sleep(5)
            try:
                api_response = \
                    self.kube_client.read_namespaced_service_status(service_name, "default", pretty='true')
                self.app.logger.info("Service status read successfully with response: \n{}\n".format(api_response))
                if api_response.status.load_balancer.ingress is not None:
                    if infra in {"EKS"}:
                        ip_address = api_response.status.load_balancer.ingress[0].hostname
                    else:
                        ip_address = api_response.status.load_balancer.ingress[0].ip
            except ApiException as e:
                self.app.logger.error("Error reading Service status: \n{}\n".format(e))

            elapsed_time = time.time() - start_time
        if ip_address:
            self.app.logger.info("Compute ip address: \n{}\n".format(ip_address))
            return ip_address
        else:
            self.app.logger.error("Failed to get compute ip address")

    def launch_pod(self, pod_body):
        try:
            api_response = self.kube_client.create_namespaced_pod("default", body=pod_body, pretty='true')
            self.app.logger.info("Pod created successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error creating Pod: \n{}\n".format(e))

    def launch_service(self, service_body):
        try:
            api_response = \
                self.kube_client.create_namespaced_service("default", body=service_body, pretty='true')
            self.app.logger.info("Service created successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error creating Service: \n{}\n".format(e))

    def launch_config_map(self, config_map_body):
        try:
            api_response = \
                self.kube_client.create_namespaced_config_map("default", body=config_map_body, pretty='true')
            self.app.logger.info("ConfigMap created successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error creating ConfigMap: \n{}\n".format(e))

    def prepare_all(self):

        self.build_service_spec()

        if self.specs.get("SERVICE") is None:
            self.app.logger.error("No service spec defined.")
        service_body = yaml.safe_load(self.specs['SERVICE'])
        self.launch_service(service_body)
        try:
            self.this_compute_ip = self._get_service_ip(f"{self.spec_prefix}-service")
        except Exception as e:
            self.app.logger.error("Failed to get compute ip address: \n{}\n".format(e))

        self._exchange_ips()
        self.build_pod_spec()
        self.build_congregation_config()
        self.build_config_map()

    def launch_all(self):

        if self.specs.get("POD") is None:
            self.app.logger.error("No pod spec defined.")

        if self.specs.get("CONFIG_MAP") is None:
            self.app.logger.error("No config map spec defined.")

        config_map_body = yaml.safe_load(self.specs['CONFIG_MAP'])
        pod_body = yaml.safe_load(self.specs['POD'])

        self.launch_config_map(config_map_body)
        self.launch_pod(pod_body)

    def stop_workflow(self):
        self.running = False  # to stop sending requests
        try:
            api_response = \
                self.kube_client.delete_namespaced_config_map(f"{self.spec_prefix}-config-map", "default", pretty='true')
            self.app.logger.info("ConfigMap deleted successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error deleting ConfigMap: \n{}\n".format(e))

        try:
            api_response = \
                self.kube_client.delete_namespaced_service(f"{self.spec_prefix}-service", "default", pretty='true')
            self.app.logger.info("Service deleted successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error deleting Service: \n{}\n".format(e))

        try:
            api_response = \
                self.kube_client.delete_namespaced_pod(f"{self.spec_prefix}-pod", "default", pretty='true')
            self.app.logger.info("Pod deleted successfully with response: \n{}\n".format(api_response))
        except ApiException as e:
            self.app.logger.error("Error deleting Pod: \n{}\n".format(e))

        if self.workflow_config['PID'] == 1:
            try:
                api_response = \
                    self.kube_client.delete_namespaced_service(f"{self.spec_prefix}-jiff-server-service", "default", pretty='true')
                self.app.logger.info("JIFF Service deleted successfully with response: \n{}\n".format(api_response))
            except ApiException as e:
                self.app.logger.error("Error deleting JIFF Service: \n{}\n".format(e))

            try:
                api_response = \
                    self.kube_client.delete_namespaced_pod(f"{self.spec_prefix}-jiff-server", "default", pretty='true')
                self.app.logger.info("JIFF Pod deleted successfully with response: \n{}\n".format(api_response))
            except ApiException as e:
                self.app.logger.error("Error deleting JIFF Pod: \n{}\n".format(e))

