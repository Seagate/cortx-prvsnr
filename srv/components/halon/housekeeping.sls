Remove temporary mini_conf file:
  file.absent:
    - name: /tmp/mini_conf.yaml

Remove temporary halon_facts file:
  file.absent:
    - name: /tmp/halon_facts.yaml
