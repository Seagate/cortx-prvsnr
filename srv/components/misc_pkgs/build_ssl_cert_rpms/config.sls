{% if pillar["cluster"][grains["id"]]["is_primary"] %}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if not pillar['cluster'][node_id]['is_primary'] %}

Copy certs to non-primary:
  cmd.run:
    - name: scp -r /opt/seagate/certs {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/

{%- endif -%}
{%- endfor -%}
{% else %}
Wait for certs to be received:
  cmd.run:
    - name: sleep 5
{% endif %}


Copy certs to s3 and s3auth directories:
  cmd.run:
    - names:
      - cp -r /opt/seagate/certs/* /etc/ssl/stx-s3/s3/
      - cp -r /opt/seagate/certs/* /etc/ssl/stx-s3/s3auth/

Clean certs:
  file.absent:
    - name: /opt/seagate/certs

#Add haproxy user:
#  module.run:
#    - groupadd.adduser: 
#      - name: certs
#      - user: haproxy
