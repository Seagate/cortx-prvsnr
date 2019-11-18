# File cleanup operation
{% for filename in [
   '/tmp/mini_conf.yaml',
   '/tmp/halon_facts.yaml'
 ] %}
{{ filename }}:
  file.absent:
    - onlyif: test -f {{ filename }}
{% endfor %}
