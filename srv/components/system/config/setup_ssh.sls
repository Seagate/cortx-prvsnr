/root/.ssh:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
    - force: True
    - recurse:
      - user
      - group
      - mode

/root/.ssh/id_rsa:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 600
    - create: True

/root/.ssh/id_rsa.pub:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr.pub
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/authorized_keys:
  file.managed:
    - source: salt://components/system/files/.ssh/authorized_keys
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/known_hosts:
  file.managed:
    - source: salt://components/system/files/.ssh/known_hosts
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True
