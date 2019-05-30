Remove temporary mini_conf file:
  file.managed:
    - name: /tmp/mini_conf.yaml

Remove temporary halon_facts file:
  file.managed:
    - name: /tmp/halon_facts.yaml
