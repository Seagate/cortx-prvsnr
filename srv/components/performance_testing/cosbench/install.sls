Install support packages:
  pkg.installed:
      - pkgs:
        - java-1.8.0-openjdk-headless.x86_64
        - nmap-ncat.x86_64

Download and extract cosbench:
  archive.extracted:
    - name: /opt
    - source: https://github.com/intel-cloud/cosbench/releases/download/v0.4.2.c3/0.4.2.c3.zip
    - keep_source: False
    - skip_verify: True
    - force: True
    - overwrite: True
    - clean: True

Rename file:
  file.rename:
    - name: /opt/cos
    - source: /opt/0.4.2.c3
    - makedirs: True
    - force: True
    - require:
      - archive: Download and extract cosbench
