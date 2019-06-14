facts:
    node_1:
        fqdn: ees-node1
        primary: yes
        mgmt_if: mgmt0
        data_if: data0
        # Metadata device
        metadata_device: /dev/sdb
        # Data drive
        data_device_1: /dev/sdc
        gateway_ip: 10.230.160.1
    node_2:
        fqdn: ees-node2
        primary: no
        mgmt_if: mgmt0
        data_if: data0
        # Metadata device
        metadata_device: /dev/sdb
        # Data drive
        data_device_1: /dev/sdc
        gateway_ip: 10.230.160.1
