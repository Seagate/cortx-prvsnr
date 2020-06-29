{% set node = grains['id'] %}
{% set data_if = pillar['cluster'][node]['network']['data_nw']['iface'] %}

Create index:
  cmd.run:
    - name: 

Initialize KVSNS:
  cmd.run:
    - name: kvsns_init

Start NFS Server:
  cmd.run:
    - name: ganesha.nfsd -L /dev/tty -F -f /etc/ganesha/ganesha.conf

Mount NFS4:
  mount.mounted:
    - name: /mnt/nfs_mount
    - device: {{ grains['ip4_interfaces'][data_if][0] }}:/kvsns
    - fstype: nfs4
    - mkmnt: True
