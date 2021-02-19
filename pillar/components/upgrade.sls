upgrade:
  sw_list:
    - motr
    - s3server
    - hare
    - ha.cortx-ha
    - sspl
    - uds
    - csm
  yum_snapshots: {} # define specific cortx-version's yum-txn-id for each node
                    # <cortx-version>:
                    #   <node-id>: <yum-txn-id>
