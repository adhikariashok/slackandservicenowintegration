import os, sys
import logging
# logging.basicConfig(level=logging.INFO) # override the debug level defined in Kentaurus
from centralstation.auth import MultiAuthClient
from kentaurus.base import Kentaurus
from dotenv import load_dotenv

load_dotenv()

app_password_prod = os.environ["app_password_prod"]
app_password_uat = os.environ["app_password_uat"]

app_id = "181289"
a3_auth_client_prod = MultiAuthClient(
    app_id, app_password_prod, env="PROD", other_app="150899"
)  # kentaurus AppID = 150899
a3_auth_client_uat = MultiAuthClient(
    app_id, app_password_uat, env="UAT", other_app="150899"
)  # kentaurus AppID = 150899

def get_kentaurus_client(env="PROD"):
    if env=="PROD":
        return Kentaurus(a3_auth_client_prod, app_id, env="PROD")
    else:
        return Kentaurus(a3_auth_client_uat, app_id, env="UAT")
