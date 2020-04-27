include:
  - components.system.storage.multipath.install

Stop multipath service:
  service.dead:
    - name: multipathd.service
    - require:
      - Install multipath

Copy multipath config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://components/system/storage/multipath/files/multipath.conf
    - force: True
    - makedirs: True
    - require:
      - Install multipath
      - Stop multipath service

# Flush multipath:
#   cmd.run:
#     - name: multipath -F

Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

{% if not pillar['cluster'][grains['id']]['is_primary'] -%}
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if pillar['cluster'][node_id]['is_primary'] %}
# Execute only on Secondary node
Copy multipath bindings to non-primary:
  cmd.run:
    - name: scp {{ pillar['cluster'][node_id]['hostname'] }}:/etc/multipath/bindings /etc/multipath/bindings
{%- endif %}
{% endfor %}
{%- endif %}

{% if pillar['cluster'][grains['id']]['is_primary'] %}
Update cluster.sls pillar:
  module.run:
    - cluster.storage_device_config: []
    - saltutil.refresh_pillar: []
    - require:
      - Start multipath service
{% else %}
Update cluster.sls pillar:
  test.show_notification:
    - text: Update pillar doesn't work on Secondary node.
{% endif %}

Restart service multipath:
  module.run:
    - service.restart:
      - multipathd
    - require:
      - Update cluster.sls pillar
# End Setup multipath
