# Overview
The rbac-builder reads a configuration yaml, and convert it to Robusta's RBAC rules.
In it, you should specify the `account_id`, `scopes` and `groups`

Each execution, the `rbac-builder` will delete all the existing `scopes` and `groups` for the account, 
and will create new ones, according to the provided configuration

This is a configuration example: (the file can be found under `config/definitions.yaml`
)
```angular2html
account_id: 6c2cbf41-c7b5-48ab-9777-76d320b985d4  # UUID
scopes:
  - name: scope-1
    type: namespace
    clusters:
      cl1: ["*"]
      cl2: ["default", "kube-system"]
  - name: scope-2
    type: cluster
    clusters:
      cl3: ["*"]
      cl4: ["*"]
groups:
  - name: dev-us-xyz
    provider_group_id: ea50b713-93c0-45d3-a87d-de253c06db0a  # UUID
    type: namespace
    permissions: ["POD_LOGS", "METRICS_VIEW", "JOB_DELETE"]
    scopes: ["scope-1"]
  - name: dev-eu-ttt
    provider_group_id: 233bd8f0-60a7-4cbc-b151-b109c3308b07  # UUID
    type: cluster
    permissions: ["CLUSTER_DELETE", "POPEYE_SCAN"]
    scopes: ["scope-1", "scope-2"]
```

# Configuration

To run this, you'll need to provide environment variable, with DB accesss parameters
Use the same credentials as the `plaform-relay` service

```angular2html
STORE_API_KEY=eyJ...
STORE_PASSWORD=e...
STORE_URL=https://...
STORE_USER=apiuser-stgrobustarelay@robusta.dev
```

If you're using self-signed certificates, add it using the `CERTIFICATE` (the same way it's added to the `platform-relay` service) 

# How To Use

`Scopes`
Each scope has a `type` field that must be `cluster` or `namespace`

`cluster` scope, means the scope is on the *entire* cluster (all namespaces)
Each cluster scope should be in the format of: `cluster-name: ["*"]`

`namespace` scope, means the scope can be on a set of namespaces, within a cluster
The format of namespaces scope is: `cluster-name: ["ns1", "ns2"]`
You can also define a `namespace` scope on all cluster namespaces: `cluster-name: ["*"]`


`Groups`
Each group has a `type` field that must be `cluster` or `namespace`

`cluster` groups, can only be applied on scopes with `type` "cluster"
`namespace` groups, can only be applied on all scopes


Every group has a set of `permissions`. These are the actual actions the user will be allowed to do.

There are default `permissions`, which are given by default to every group.

For `namespace` groups, the default permissions are: `APP_VIEW, JOB_VIEW, TIMELINE_VIEW`
For `cluster` groups, the default permissions are: `APP_VIEW, JOB_VIEW, TIMELINE_VIEW, NODE_VIEW, CLUSTER_VIEW`

`namespace` groups can be assigned to one of the following permissions (on top of the default permissions):
`APP_RESTART, JOB_DELETE, POD_LOGS, POD_DELETE, KRR_VIEW, POPEYE_VIEW, METRICS_VIEW`

`cluster` groups can be assigned to one of the following permissions (on top of the default permissions):
`APP_RESTART, JOB_DELETE, POD_LOGS, POD_DELETE, METRICS_VIEW, NODE_DRAIN, NODE_CORDON, NODE_UNCORDON, CLUSTER_DELETE, KRR_SCAN, KRR_VIEW, POPEYE_VIEW, POPEYE_SCAN, ALERT_CONFIG_EDIT, ALERT_CONFIG_VIEW, SILENCES_VIEW, SILENCES_EDIT`

# Deployment
TBD


