Extract Node.js:
  archive.extracted:
    - name: /opt/nodejs
    - source: https://nodejs.org/dist/v12.13.0/node-v12.13.0-linux-x64.tar.xz
    - source_hash: https://nodejs.org/dist/v12.13.0/SHASUMS256.txt.asc
    - source_hash_name: node-v12.13.0-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: False

Apppend bash_profile:
  file.blockreplace:
    - name: ~/.bash_profile
    - marker_start: '# DO NOT EDIT: Nodejs'
    - marker_end: '# DO NOT EDIT: End'
    - content: |
        VERSION=v12.13.0
        DISTRO=linux-x64
        export PATH=/opt/nodejs/node-$VERSION-$DISTRO/bin:$PATH
    - backup: '.org'
    - append_if_not_found: True
    - require:
      - archive: Extract Node.js

Refresh bash_profile:
  cmd.run:
    - name: source ~/.bash_profile
    - require:
      - file: Apppend bash_profile

Install csm package:
  pkg.installed:
    - name: eos_csm
