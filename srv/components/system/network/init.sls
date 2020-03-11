{% if pillar['cluster'][grains['id']]['network']['gateway_ip'] %}
include:
  - components.system.network.prepare
  - components.system.network.install
  - components.system.network.config
  - components.system.network.direct
  # - components.system.network.mgmt

{% else %}
Network config failure:
  test.fail_without_changes:
    - name: Network configuration in absense of Gateway IP results in node inaccessibility.
{% endif %}