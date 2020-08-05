salt_minion_configured:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://provisioner/files/minions/all/minion
    - keep_source: True
    - backup: minion
    - template: jinja

# FIXME CORTX-8473 prepend is not a clean solution
salt_minion_grains_configured:
  file.prepend:
    - name: /etc/salt/grains
    - sources:
      - salt://provisioner/files/minions/all/cluster_id
      - salt://provisioner/files/minions/{{ grains.id }}/grains
      - salt://provisioner/files/minions/{{ grains.id }}/node_id
      - salt://provisioner/files/minions/{{ grains.id }}/hostname_status

# TODO CORTX-8473 better content management
salt_minion_id_set:
  file.prepend:
    - name: /etc/salt/minion_id
    - text: {{ grains.id }}

salt_minion_pki_set:
  file.recurse:
    - name: /etc/salt/pki/minion
    - source: salt://provisioner/files/minions/{{ grains.id }}/pki
    - clean: True
    - keep_source: True
    - maxdepth: 0

salt_minion_master_pki_set:
  file.managed:
    - name: /etc/salt/pki/minion/minion_master.pub
    - source: salt://provisioner/files/master/pki/master.pub
    - keep_source: True
    - backup: minion
    - template: jinja

salt_minion_enabled:
  service.enabled:
    - name: salt-minion.service
    - require:
      - salt_minion_configured
      - salt_minion_grains_configured
      - salt_minion_id_set
      - salt_minion_pki_set
      - salt_minion_master_pki_set

salt_minion_stopped:
  service.dead:
    - name: salt-minion.service
    - watch:
      - file: salt_minion_configured
      - file: salt_minion_grains_configured
      - file: salt_minion_id_set
      - file: salt_minion_pki_set
      - file: salt_minion_master_pki_set
