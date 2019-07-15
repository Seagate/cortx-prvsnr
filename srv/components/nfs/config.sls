Create index:
  cmd.run:
    - name: m0clovis -l {{ pillar['nfs']['local_addr'] }} -h {{ pillar['nfs']['ha_addr'] }} -p '{{ pillar['nfs']['profile'] }}' -f '\{{{ pillar['nfs']['proc_fid'] }}\}' index create "{{ pillar['nfs']['kvs_fid'] }}"

Initialize KVSNS:
  cmd.run:
    - name: kvsns_init

Start NFS Server:
  cmd.run:
    - name: ganesha.nfsd -L /dev/tty -F -f /etc/ganesha/ganesha.conf

Mount NFS4:
  mount.mounted:
    - name: /mnt/nfs_mount
    - device: {{ grains['ip_interfaces']['data0'][0] }}:/kvsns
    - fstype: nfs4
    - mkmnt: True
