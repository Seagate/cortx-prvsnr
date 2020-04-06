{% set node_version = pillar['commons']['version']['nodejs'] %}
# Sanity check
Check nodejs version:
  cmd.run:
    - name: /opt/nodejs/node-{{ node_version }}-linux-x64/bin/node -v
    - require:
      - Extract Node.js
