{% if pillar["cluster"][grains["id"]]["is_primary"] %}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if not pillar['cluster'][node_id]['is_primary'] %}

Copy certs to non-primary:
  cmd.run:
    - name: scp -r /opt/seagate/certs {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/

{%- endif -%}
{%- endfor -%}
{% endif %}


Copy certs to s3 and s3auth directories:
  file.recurse:
    - names:
      - /etc/ssl/stx-s3/s3
      - /etc/ssl/stx-s3/s3auth
    - source: /opt/seagate/certs/*
    - keep_source: False
    - clean: False
    - user: certs
    - group certs 
    - dir_mode: 755
    - file_mode: 644

Clean certs:
  file.absent:
    - name: /opt/seagate/certs

#Add haproxy user:
#  module.run:
#    - groupadd.adduser: 
#      - name: certs
#      - user: haproxy
