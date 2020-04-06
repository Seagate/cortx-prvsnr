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
    - source: http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/csm_uploads/{{ node_version }}/node-{{ node_version }}-linux-x64.tar.xz
    - source_hash: http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/csm_uploads/{{ node_version }}/SHASUMS256.txt.asc
    - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True
