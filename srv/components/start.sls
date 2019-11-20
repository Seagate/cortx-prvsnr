include:
  - components.sspl.start
  - components.halon.start
  - components.eoscore.start
  - components.s3server.start
  - components.ha.haproxy.start

{% set node = grains['id'] %}

{% if salt['service.status']('halond.service') and pillar['cluster'][node]['is_primary'] %}
Start cluster:
  cmd.run:
    - name: hctl mero start
{% endif %}


