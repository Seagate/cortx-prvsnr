Ensure halond service running:
  service.running:
    - name: halond

# Generate mini_conf.yaml
Prepare mini_conf file:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/mini_conf.yaml
    - source: salt://components/halon/files/mini_conf.yaml
    - template: jinja

{% if 'mgmt0' in grains['ip4_interfaces'] %}
  {% set mgmt_nw = 'mgmt0' %}
{% else %}
  {% set mgmt_nw = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] %}
{% endif %}
# Generate Halon facts file
Generate halon_facts.yaml file:
  cmd.run:
    - name: m0genfacts -o /opt/seagate/eos-prvsnr/generated_configs/halon_facts.yaml -c /opt/seagate/eos-prvsnr/generated_configs/mini_conf.yaml -e data0 -E {{ mgmt_nw }} -N 1 -K 0
    - require:
      - file: Prepare mini_conf file

#To be verified manually
Copy halon_facts.yaml to /etc/halon:
  cmd.run:
    - name: cp /opt/seagate/eos-prvsnr/generated_configs/halon_facts.yaml /etc/halon/halon_facts.yaml
    - onlyif: test -f /opt/seagate/eos-prvsnr/generated_configs/halon_facts.yaml
    - require:
      - Generate halon_facts.yaml file

# Create a file /etc/halon/bootstrap.ready to indicate that the node is ready for bootstrap
Touch bootstrap.ready file:
  cmd.run:
    - name: touch /etc/halon/bootstrap.ready
    - onlyif: test -f /etc/halon/halon_facts.yaml
    - require:
      - Copy halon_facts.yaml to /etc/halon
