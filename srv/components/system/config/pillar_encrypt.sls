Encrypt_pillar:
  cmd.run:
    - name: python3 /opt/seagate/cortx/provisioner/cli/pillar_encrypt

Refresh pillar data:
  module.run:
    - saltutil.refresh_pillar: []
