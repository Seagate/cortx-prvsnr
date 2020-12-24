{% import_yaml 'components/defaults.yaml' as defaults %}

{% set node_version = pillar['commons']['version']['nodejs'] %}
# Nodejs install
# Extract Node.js:
#   archive.extracted:
#     - name: /opt/nodejs
#     - source: http://nodejs.org/dist/{{ node_version }}/node-{{ node_version }}-linux-x64.tar.xz
#     - source_hash: http://nodejs.org/dist/{{ node_version }}/SHASUMS256.txt.asc
#     - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
#     - keep_source: True
#     - clean: True
#     - trim_output: True

Extract Node.js:
  archive.extracted:
    - name: /opt/nodejs
    - source: {{ defaults.commons.repo.url }}/commons/node/node-v12.13.0-linux-x64.tar.xz
    - source_hash: {{ defaults.commons.repo.url }}/commons/node/SHASUMS256.txt.asc
    - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True
