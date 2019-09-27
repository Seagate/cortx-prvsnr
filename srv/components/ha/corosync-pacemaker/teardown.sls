
Stop Cluster:
  cmd.run:
    - name: pcs cluster stop --force

Destroy Cluster:
  cmd.run:
    - name: pcs cluster destroy

Remove user and group:
  cmd.run:
    - names: 
      - userdel {{ pillar['csm']['user'] }}
      - groupdel haclient

Remove pcs package:
  pkg.purged:
    - pkgs:
      - pcs
      - pacemaker
      - corosync

Enable and Start Firewall:
  cmd.run:
    - names:
      - systemctl enable firewalld
      - systemctl start firewalld
