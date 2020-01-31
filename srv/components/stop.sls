{% set node = grains['id'] %}

{% if not salt['service.status']('halond.service') and pillar['cluster'][node]['is_primary'] %}

{% set cluster_status = salt['cmd.shell']('hctl mero status --json') %}
{% if "ONLINE" in cluster_status %}
Stop cluster:
  cmd.run:
    - name: hctl mero stop
{% endif %}

{% endif %}

include:
  - components.ha.haproxy.stop
  - components.s3server.stop
  - components.eoscore.stop
  - components.hare.stop
  - components.sspl.stop

Stop rabbitmq-server:
  service.dead:
    - name: rabbitmq-server
