# Provisioner Code Design Updates

Table of Contents:

- [Scope](#scope)
- [ClusterID API design](#clusterid-api-design)
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


## Storage CVG Keys

TB Added

## CES Workflow

TB Added
