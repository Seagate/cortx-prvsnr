Extract Node.js:
  archive.extracted:
    - name: /opt/nodejs
    - source: https://nodejs.org/dist/v12.13.0/node-v12.13.0-linux-x64.tar.xz
    - source_hash: https://nodejs.org/dist/v12.13.0/SHASUMS256.txt.asc
    - source_hash_name: node-v12.13.0-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True
