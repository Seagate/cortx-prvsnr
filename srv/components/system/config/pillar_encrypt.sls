Encrypt_pillar:
  cmd.run:
    {% if salt['file.file_exists']("/opt/seagate/cortx/provisioner/cli/pillar_encrypt") %}
    - name: python3 /opt/seagate/cortx/provisioner/cli/pillar_encrypt       # Prod env
    {% else %}
    - name: python3 /opt/seagate/cortx/provisioner/cli/src/pillar_encrypt   # Dev env
    {% endif %}

Refresh pillar data:
  module.run:
    - saltutil.refresh_pillar: []
