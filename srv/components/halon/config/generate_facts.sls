{% set node = grains['id'] %}

Ensure halond service running:
  service.running:
    - name: halond

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

# Create a file /etc/halon/bootstrap.ready to indicate that the node is ready for bootstrap
Touch bootstrap.ready file:
  cmd.run:
    - name: touch /etc/halon/bootstrap.ready
    - onlyif: test -f /etc/halon/halon_facts.yaml
    - require:
      - Copy halon_facts.yaml to /etc/halon
