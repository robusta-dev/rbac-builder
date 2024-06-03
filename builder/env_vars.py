import os

from typing import List

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


# robusta permission groups
# ADMIN_PERMISSIONS: List[str] = os.environ.get(
#     "ADMIN_PERMISSIONS",
#     "APP_VIEW,JOB_VIEW,TIMELINE_VIEW,APP_RESTART,JOB_DELETE,POD_LOGS,POD_DELETE,METRICS_VIEW,KRR_VIEW,POPEYE_VIEW").split(",")
ADMIN_PERMISSIONS: List[str] = os.environ.get(
    "ADMIN_PERMISSIONS",
    "APP_VIEW,JOB_VIEW,TIMELINE_VIEW,POD_LOGS,METRICS_VIEW,KRR_VIEW,POPEYE_VIEW").split(",")
VIEWER_PERMISSIONS: List[str] = os.environ.get(
    "VIEWER_PERMISSIONS",
    "APP_VIEW,JOB_VIEW,TIMELINE_VIEW,POD_LOGS,METRICS_VIEW,KRR_VIEW,POPEYE_VIEW").split(",")

# db store
STORE_URL = os.environ.get("STORE_URL", "")
STORE_API_KEY = os.environ.get("STORE_API_KEY", "")
STORE_USER = os.environ.get("STORE_USER", "")
STORE_PASSWORD = os.environ.get("STORE_PASSWORD", "")

# robusta platform
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "")
ACCOUNT_SSO_GROUP = os.environ.get("ACCOUNT_SSO_GROUP", "")

ALLOWED_USERS = [user.strip() for user in os.environ.get("ALLOWED_USERS", "").split(",") if user]
CLUSTER_ADMIN_GROUPS_VAR = os.environ.get("CLUSTER_ADMIN_GROUPS", "")

# format is: "eu-at-5:arik,natan,christine|eu-at-10:xxx,yyy,zzz"
CLUSTER_ADMIN_GROUPS = {}
for cluster_group in CLUSTER_ADMIN_GROUPS_VAR.split("|"):
    if cluster_group:
        cluster_name = cluster_group.split(":")[0].strip()
        group_users = cluster_group.split(":")[1].split(",")
        CLUSTER_ADMIN_GROUPS[cluster_name] = [group_user.strip() for group_user in group_users if group_user]