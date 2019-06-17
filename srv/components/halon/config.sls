{% import_yaml 'components/defaults.yaml' as defaults %}

{% set node = 'node_1' if grains['fqdn'] == pillar['facts']['node_1']['fqdn'] else 'node_2' if grains['fqdn'] == pillar['facts']['node_2']['fqdn'] else None %}

{% set mgmt_if = salt["pillar.get"]("facts:{0}:mgmt_if".format(node), "lo") %}
{% set data_if = salt["pillar.get"]("facts:{0}:data_if".format(node), "lo") %}

# Configure halond
Update Halon config file:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents:
      - HALOND_LISTEN={{ grains["ip4_interfaces"][mgmt_if][0] }}:9070
      - HALOND_STATION_OPTIONS="--rs-lease 4000000"
    - user: root
    - group: root

# Setup Halon service
Service Halon startup:
  service.running:
    - name: halond
    - enable: True
    - watch:
      - file: Update Halon config file

# Generate mini_conf.yaml
Prepare mini_conf file:
  file.managed:
    - name: /tmp/mini_conf.yaml
    - source: salt://components/halon/files/mini_conf.yaml
    - template: jinja

# Generate Halon facts file
Generate halon_facts.yaml file:
  cmd.run:
    - name: m0genfacts -o /tmp/halon_facts.yaml -c /tmp/mini_conf.yaml -e {{ data_if }} -E {{ mgmt_if }} -N 1 -K 0
    - require:
      - file: Prepare mini_conf file

#To be verified manually
Copy halon_facts.yaml to /etc/halon:
  cmd.run:
    - name: cp /tmp/halon_facts.yaml /etc/halon/halon_facts.yaml
    - onlyif: test -f /tmp/halon_facts.yaml
    - require:
      - Generate halon_facts.yaml file
