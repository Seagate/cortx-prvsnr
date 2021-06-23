# Provisioner Code Design Updates

Table of Contents:

- [Scope](#scope)
- [ClusterID API design](#clusterid-api-design)
- [LR CLI design](#lr-cli-design)
- [Storage CVG Keys](#storage-cvg-keys)
- [CES Workflow](#ces-workflow)


## Scope

The scope of this article is to document the design discussions (internal and external) and major code updates happening for Provisioner module.
The discussion points are captured in **Outcome** and **Reason** sections. This helps the team stay informed about the design changes and the reason why we move to the latest changes.


## ClusterID API design

**Outcome:**
The explicit Get/Set functions of cluster_id are muted and we move to a generic API as,
```
provisioner cluster_id
```

If the `cluster_id` is configured and unique, this API returns the value of it.
If not, it sets the value in pillar and then fetches that value and returns to the user.

**Reason:**
`cluster_id` is a significant parameter which must be maintained unique at all times and is one of the seeds for cryptography key generation. Any change or manual modification to this value will take the entire cluster up for a toss.  And, in any case of misuse of `set`, the whole setup is compromised.

**Implementation:**
To avoid this, these are suggested actions:

* Add `cluster_id` to a dedicated file, namely, `/etc/cluster-id` and make the file immutable.
* Add the same cluster_id value to pillar `cluster:cluster_id`.

We then cross-verify the 2 keys everytime a `get` operation is called.

NOTE: The API will NOT take any mandatory input parameter from the user.

**Why no `get`?**   
This is simply to avoid confusion. A generic call like `hostname` should take care of both set and get. We do not want to reset cluster_id if it's already set.
A simple warning in `provisioner cluster_id` is better, and less harmful than `provisoner set_cluster_id "some_id_string"` refusing to set the value and throwing error. (This also keeps everyone on same page and helps to avoid any convincing of this API behavior for no apparent reason)

So the idea is to have a class `ClusterId`:

* In a separate initial method or the `__init__` of the class, we check if the `/etc/cluster-id` file exists and has a value, and if not, set a value and set this file to be immutable.
* Then, check if pillar `cluster:cluster_id` is set and has the same value, and if not, set the value from the grain.
* Set the cluster_id value from this initial method or the `__init__` call to `ClusterId().cluster_id`. This also takes care of codacy crib regarding self not used in method.
* In `ClusterId().run()`, i.e. the actual command call of `provisioner cluster_id`, return only the value of `cluster_id`.


## LR CLI design

**Outcome:**   

To handle Factory and Field configurations and processes, a separate API is created named `cortx_setup`.
```
cortx_setup <process> <operation> --params
```
Example,
```
cortx_setup signature get <key> 
cortx_setup network config <transport_type> 
```

**Reason:**   
Reference Confluence pages for the above design creation:
1. [Factory Manufacturing implementation](https://seagate-systems.atlassian.net/wiki/spaces/PRIVATECOR/pages/221642873/CORTX+Factory+Manufacturing+Process)

2. [Field Deployment implementation](https://seagate-systems.atlassian.net/wiki/spaces/PRIVATECOR/pages/221642890/CORTX+Field+Deployment+Process)

**Pre-req:**   
`cortx_setup` API uses existing Salt functionalities and some provisioner utilities. So, for this new API to be available, provisioner rpm should be installed and present in the environment. Post that, install `cortx_setup` API,

```
pip3 install lr-cli/
```

**Implementation:**   
This implementation is placed under LR directory, separate from Provisioner API design.
A simple, straightforward CLI design is created to execute these APIs.

Following files must be updated for every new command implementation,

1. `lr-cli/setup.py`
2. `lr-cli/api_spec.yaml`
3. `lr-cli/commands/__init__.py`
4. `lr-cli/commands/<new_API>`

**Dir structure:**
```bash
cortx-prvsnr/
├── lr-cli/
│   ├── cortx_setup/
│   │   ├── api_spec.yaml
│   │   ├── commands/
│   │   │   ├── command.py
│   │   │   ├── __init__.py
│   │   │   ├── network/
│   │   │   │   ├── config.py
│   │   │   ├── node/
│   │   │   │   ├── initialize.py
│   │   │   └── signature/
│   │   │       ├── get.py
│   │   │       └── set.py
│   │   ├── log.py
│   │   ├── main.py
│   ├── MANIFEST.in
└── └── setup.py
```

### Field API design changes


1. **Cluster create - Bootstrap:**   
Currently, nodes to be clustered are getting fetched from the user as input `nodes`. But this param is not required and it must be automatically fetched from the list of salt keys (from `salt-key -L` command).   
For this to be in place, before executing bootstrap, we'd need the node hostname to be updated as minion_id instead of `srvnode-0`. A separate API might be needed for this purpose.   


## Storage CVG Keys

TB Added

## CES Workflow

TB Added
