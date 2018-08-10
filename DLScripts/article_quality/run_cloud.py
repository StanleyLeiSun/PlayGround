#!/home/stansun/tools/p2tf/bin/python2

import yaml
import os
from fds.galaxy_fds_client import GalaxyFDSClient
from fds.galaxy_fds_client_exception import GalaxyFDSClientException
from fds.fds_client_configuration import FDSClientConfiguration

config_filename = os.path.join(os.path.expanduser("~"), ".config/xiaomi/config")
with open(config_filename) as f:
    config_data = yaml.safe_load(f)

access_key = config_data["xiaomi_cloudml"]["xiaomi_access_key_id"]
secret_key = config_data["xiaomi_cloudml"]["xiaomi_secret_access_key"]
fds_endpoint = config_data["xiaomi_cloudml"]["xiaomi_fds_endpoint"]

config = FDSClientConfiguration(
    region_name="cnbj1-fds",
    enable_https=False,
    enable_cdn_for_upload=False,
    enable_cdn_for_download=False,
    endpoint=fds_endpoint)

fds_client = GalaxyFDSClient(access_key, access_secret, config)

client.put_object(

#cloudml jobs submit -n article-quality-local -m lstm_training -g 1 -M 8G -u fds://training/packages/article-quality-1.1.tar.gz


