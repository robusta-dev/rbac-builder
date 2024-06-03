import uuid
from typing import List, Dict

import pydantic
import yaml
from pydantic import BaseModel, field_validator

from builder.model import RobustaPermissionScope, RobustaPermissionGroup

MINIMAL_NAMESPACE_PERMISSIONS: List[str] = ["APP_VIEW","JOB_VIEW","TIMELINE_VIEW"]
MINIMAL_CLUSTER_PERMISSIONS: List[str] = ["APP_VIEW","JOB_VIEW","TIMELINE_VIEW","NODE_VIEW","CLUSTER_VIEW"]

NAMESPACE_PERMISSIONS: List[str] = ["APP_VIEW","JOB_VIEW","TIMELINE_VIEW","APP_RESTART","JOB_DELETE","POD_LOGS",
                                    "POD_DELETE","KRR_VIEW","POPEYE_VIEW","METRICS_VIEW"]
CLUSTER_PERMISSIONS: List[str] = ["APP_VIEW","JOB_VIEW","TIMELINE_VIEW","NODE_VIEW","CLUSTER_VIEW","APP_RESTART",
                                  "JOB_DELETE","POD_LOGS","POD_DELETE","METRICS_VIEW","NODE_DRAIN","NODE_CORDON",
                                  "NODE_UNCORDON","CLUSTER_DELETE","KRR_SCAN","KRR_VIEW","POPEYE_VIEW","POPEYE_SCAN",
                                  "ALERT_CONFIG_EDIT","ALERT_CONFIG_VIEW","SILENCES_VIEW","SILENCES_EDIT"]


class RobustaScopeDefinition(BaseModel):
    type: str
    name: str
    clusters: Dict[str, List[str]]

    @field_validator("type", mode="after")
    def validate_type(cls, v):
        if v not in ["namespace", "cluster"]:
            raise ValueError("Scope type must be either 'namespace' or 'cluster'")
        return v


class RobustaGroupDefinition(BaseModel):
    name: str
    type: str
    provider_group_id: str
    scopes: List[str]
    permissions: List[str]

    @field_validator("type", mode="after")
    def validate_type(cls, v):
        if v not in ["namespace", "cluster"]:
            raise ValueError("Group type must be either 'namespace' or 'cluster'")
        return v


class ConfigDefinition(BaseModel):
    account_id: str
    scopes: List[RobustaScopeDefinition]
    groups: List[RobustaGroupDefinition]

    @field_validator("scopes", mode="after")
    def validate_scopes(cls, scopes):
        if not isinstance(scopes, List):
            raise ValueError("Scopes must be a list")

        for scope in scopes:
            if not isinstance(scope, RobustaScopeDefinition):
                raise ValueError(f"Unknown scope type {type(scope)}")

            if scope.type == "cluster":
                for cluster_namespaces in scope.clusters.values():
                    if len(cluster_namespaces) != 1 or "*" not in cluster_namespaces:
                        raise ValueError("Cluster scope must contain only one '*' and not specific namespaces")

        return scopes

    @field_validator("groups", mode="after")
    def validate_groups(cls, groups):
        if not isinstance(groups, List):
            raise ValueError("Groups must be a list")

        for group in groups:
            if not isinstance(group, RobustaGroupDefinition):
                raise ValueError(f"Unknown group type {type(group)}")

            minimal_permissions = MINIMAL_CLUSTER_PERMISSIONS if group.type == "cluster" \
                else MINIMAL_NAMESPACE_PERMISSIONS
            all_permissions = CLUSTER_PERMISSIONS if group.type == "cluster" else NAMESPACE_PERMISSIONS
            group_permissions: List[str] = []
            group_permissions.extend(minimal_permissions)

            for permission in group.permissions:
                if permission not in all_permissions:
                    raise ValueError(f"Unknown permission {permission}")
                if permission not in group_permissions:
                    group_permissions.append(permission)

            group.permissions = group_permissions

        return groups

    @pydantic.model_validator(mode="after")
    def validate_config(self):
        groups = self.groups
        scopes = {scope.name: scope for scope in self.scopes}
        for group in groups:
            for group_scope_name in group.scopes:
                scope = scopes.get(group_scope_name, None)
                if not scope:
                    raise ValueError(f"Group {group.name} scope {group_scope_name} doesn't exist")
                if group.type == "cluster" and scope.type == "namespace":
                    raise ValueError(f"Group {group.name} is 'cluster' type. "
                                     f"Cannot be assigned to namespace scope {group_scope_name}")
        return self


class ConfigBuilder:

    def __init__(self, config_file_name: str):
        with open(config_file_name, "r") as conf_file:
            yaml_content = yaml.safe_load(conf_file)
            self.config = ConfigDefinition(**yaml_content)

        self.account_id = self.config.account_id
        self.scopes = [RobustaPermissionScope(
            account_id=self.account_id,
            scope_type=scope.type,
            scope_id=str(uuid.uuid4()),
            name=scope.name,
            scope_data=scope.clusters
        ) for scope in self.config.scopes]

        scopes_by_name = {scope.name: scope for scope in self.scopes}

        self.groups = [RobustaPermissionGroup(
            account_id=self.account_id,
            group_id=str(uuid.uuid4()),
            provider_group_id=group.provider_group_id,
            name=group.name,
            scope_type=group.type,
            scopes=[scopes_by_name[scope].scope_id for scope in group.scopes],  # convert to reference by id
            permissions=group.permissions
        ) for group in self.config.groups]

    def get_scopes(self) -> List[RobustaPermissionScope]:
        return self.scopes

    def get_groups(self) -> List[RobustaPermissionGroup]:
        return self.groups

    def get_account_id(self) -> str:
        return self.account_id