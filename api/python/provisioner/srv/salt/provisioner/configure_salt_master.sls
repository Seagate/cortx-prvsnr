# TODO IMPROVE EOS-8473 move to pillar to make configurable
{% set install_dir = '/opt/seagate/cortx/provisioner' %}
{% set salt_master_running = salt['service.status']('salt-master') %}

salt_master_configured:
  file.managed:
    - name: /etc/salt/master
    - source: {{ install_dir }}/srv/components/provisioner/salt_master/files/master
    - keep_source: True
    - backup: minion

{% for id in salt['pillar.get']('updated_keys', []) %}
salt_minion_{{ id }}_key_deleted:
  cmd.run:
    - name: salt-key -d {{ id }} -y
{% endfor %}

salt_master_pki_set:
  file.recurse:
    - name: /etc/salt/pki/master/minions/
    - source: salt://provisioner/files/master/pki
    - clean: False
    - keep_source: True
    - maxdepth: 0

salt_master_enabled:
  service.enabled:
    - name: salt-master.service
    - require:
      - salt_master_configured
      - salt_master_pki_set

salt_master_restarted:
  service.running:
    - name: salt-master.service
    - watch:
      - file: salt_master_configured
      - file: salt_master_pki_set
