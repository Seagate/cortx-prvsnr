##Config Halon

# Generate mini_conf.yaml
mini_conf_copy:
  file.managed:
    - name: /tmp/mini_conf.yaml
    - source: salt://components/halon/files/mini_conf.yaml

# Generate Halon facts file
generate_halon_facts:
  cmd.run:
    - name: m0genfacts -o /tmp/halon_facts.yaml -i /tmp/mini_conf.yaml -e data0 -E mgmt0 -N 1 -K 2
    - require:
      - file: mini_conf_copy

To be done manually
copy_halon_facts:
  cmd.run:
    - name: cp /tmp/halon_facts.yaml /etc/halon/halon_facts.yaml
    - onlyif: test -f ./halon_facts.yaml
