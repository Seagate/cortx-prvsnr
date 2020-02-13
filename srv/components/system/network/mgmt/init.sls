{%- if pillar['cluster'][grains['id']]['network']['gateway_ip'] %}
include:
  - components.system.network.mgmt.prepare
  - components.system.network.mgmt.install
  - components.system.network.mgmt.config
{% else %}
Management network config failure:
  test.fail_without_changes:
    - name: Network configuration in absense of Gateway IP results in node inaccessibility.
{% endif %}