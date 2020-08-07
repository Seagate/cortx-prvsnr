# TODO TEST EOS-8473

{% for node_id, node in pillar['node_specs'].items() %}
    {% if node_id != grains['id'] %}

check_{{ node_id }}_reachable:
  cmd.run:
    - name: ssh -q -o "ConnectTimeout=5" {{ node_id }} exit

    {% endif %}
{% endfor %}
