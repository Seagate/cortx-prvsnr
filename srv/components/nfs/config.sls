{% set node = grains['id'] %}
{% set data_if = pillar['cluster'][node]['network']['data_if'][0] %}

Create index:
  cmd.run:
    - name: m0clovis -l {{ grains['ip_interfaces'][data_if][0] }}@tcp:12345:44:301 -h {{ grains['ip_interfaces'][data_if][0] }}@tcp:12345:45:1 -p '0x7000000000000001:1' -f '0x7200000000000000:0' index create "0x780000000000000b:1"

Initialize KVSNS:
  cmd.run:
    - name: kvsns_init

Start NFS Server:
  cmd.run:
    - name: ganesha.nfsd -L /dev/tty -F -f /etc/ganesha/ganesha.conf

Mount NFS4:
  mount.mounted:
    - name: /mnt/nfs_mount
    - device: {{ grains['ip_interfaces'][data_if][0] }}:/kvsns
    - fstype: nfs4
    - mkmnt: True
