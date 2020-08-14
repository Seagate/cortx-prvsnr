{% set node_version = pillar['commons']['version']['nodejs'] %}
{% set node_url = pillar['commons']['nodejs_repo'] %}
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
    - source: {{ node_url }}/node-{{ node_version }}-linux-x64.tar.xz
    - source_hash: {{ node_url }}/SHASUMS256.txt.asc
    - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True
