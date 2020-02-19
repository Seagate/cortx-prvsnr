{%
  if salt['file.file_exists']('/etc/multipath.conf')
  and not salt['file.file_exists']('/etc/multipath.conf.org') 
%}
Backup multipath config:
  file.copy:
    - name: /etc/multipath.conf.org
    - source: /etc/multipath.conf
    - force: True
    - makedirs: True
{% endif %}

Stop multipath service:
  service.dead:
    - name: multipathd.service

Copy multipath config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://components/system/storage/multipath/files/multipath.conf
    - force: True
    - makedirs: True
    - require:
      - service: Stop multipath service

# Flush multipath:
#   cmd.run:
#     - name: multipath -F

Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

{%- if pillar['cluster'][grains['id']]['is_primary'] %}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if not pillar['cluster'][node_id]['is_primary'] %}
Copy multipath bindings to non-primary:
  cmd.run:
    - name: scp /etc/multipath/bindings {{ pillar['cluster'][node_id]['hostname'] }}:/etc/multipath/bindings
{% endif %}
{% endfor %}
{% endif %}

Restart service multipath:
  module.run:
    - service.restart:
      - multipathd

Update cluster.sls pillar:
  module.run:
    - cluster.storage_device_config: []

# End Setup multipath
