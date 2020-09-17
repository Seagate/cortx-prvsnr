{%- if pillar['cluster']['cluster_ip'] %}
{%- set data_ip = pillar['cluster']['cluster_ip'] %}
{%- else %}
{%- set data_ip_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] %}
{%- set data_ip = grains['ip4_interfaces'][data_ip_if][0] %}
{%- endif -%}

Append /etc/hosts:
  file.replace:
    - name: /etc/hosts
    - pattern: ^\S* s3.seagate.com .*
    - repl: {{ data_ip }} s3.seagate.com sts.seagate.com iam.seagate.com sts.cloud.seagate.com
    - append_if_not_found: True

