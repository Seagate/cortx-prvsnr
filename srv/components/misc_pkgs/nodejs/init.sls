{% set node_version = pillar['commons']['version']['nodejs'] %}

# Nodejs install
Extract Node.js:
  archive.extracted:
    - name: /opt/nodejs
    - source: http://nodejs.org/dist/{{ node_version }}/node-{{ node_version }}-linux-x64.tar.xz
    - source_hash: http://nodejs.org/dist/{{ node_version }}/SHASUMS256.txt.asc
    - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True

# # System config
# Set nodejs in bash_profile:
#   file.blockreplace:
#     - name: ~/.bashrc
#     - marker_start: '# DO NOT EDIT: Nodejs binaries'
#     - marker_end: '# DO NOT EDIT: End'
#     - content: 'export PATH=/opt/nodejs/node-{{ node_version }}-linux-x64/bin:$PATH'
#     - append_if_not_found: True
#     - append_newline: True
#     - backup: False
#     - onchanges:
#       - Extract Node.js

# Source bash_profile for consul addition:
#   cmd.run:
#     - name: source ~/.bashrc
#     - watch:
#       - Set nodejs in bash_profile

# Sanity check
Check nodejs version:
  cmd.run:
    - name: /opt/nodejs/node-{{ node_version }}-linux-x64/bin/node -v
    - require:
      - Extract Node.js
    - watch:
      - Source bash_profile for consul addition
