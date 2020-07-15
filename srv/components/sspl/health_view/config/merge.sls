include:
  - .generate

{% if pillar["cluster"][grains["id"]]["is_primary"] and 'single' not in pillar['cluster']['type']%}
Merge healthschema:
  module.run:
    - sspl.merge_health_map_schema:
      - source_json: /tmp/resource_health_view.json
    - require:
      - Run Resource Health View
{% else %}
Merge healthschema:
  test.show_notification:
    - text: "Merge happens only on firstnode."
{% endif %}
