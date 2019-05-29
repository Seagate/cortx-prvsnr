{% import_yaml 'components/defaults.yaml' as defaults %}

{% set node = 'node_1' if grains['host'] == salt["pillar.get"]('facts:node_1:fqdn') else 'node_2' if grains['host'] == salt["pillar.get"]('facts:node_1:fqdn') else None %}

{% set mgmt_if = salt["pillar.get"]("facts:{0}:mgmt_if".format(node), "lo") %}
{% set data_if = salt["pillar.get"]('facts:{0}:data_if'.format(node), "lo") %}

# Configure halond
halon_conf:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents:
      - HALOND_LISTEN={{ salt["grains.get"]("ip4_interfaces:{0}:0".format(mgmt_if)) }}:9070
      - HALOND_STATION_OPTIONS="--rs-lease 4000000"
    - user: root
    - group: root

# Setup Halon service
halon_service:
  service.running:
    - name: halond
    - enable: True
    - watch:
      - file: halon_conf

# Generate mini_conf.yaml
mini_conf_copy:
  file.managed:
    - name: /tmp/mini_conf.yaml
    - source: salt://components/halon/files/mini_conf.yaml
    - template: jinja

# Generate Halon facts file
generate_halon_facts:
  cmd.run:
    - name: m0genfacts -o /tmp/halon_facts.yaml -c /tmp/mini_conf.yaml -e {{ data_if }} -E {{ mgmt_if }} -N 1 -K 0
    - require:
      - file: mini_conf_copy

#To be verified manually
copy_halon_facts:
  cmd.run:
    - name: cp /tmp/halon_facts.yaml /etc/halon/halon_facts.yaml
    - onlyif: test -f /tmp/halon_facts.yaml
    - require:
      - generate_halon_facts
