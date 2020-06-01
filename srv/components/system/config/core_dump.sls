Relocate core dump to /var/crash:
  sysctl.present:
    - name: kernel.core_pattern
    - value: '|/bin/sh -c $@ -- eval exec gzip --fast > /var/crash/core-%e.%p.gz'
    - config: /etc/sysctl.d/200-motr-dumps.conf

Load updated sysctl settings:
  cmd.run:
    - name: sysctl -p /etc/sysctl.d/200-motr-dumps.conf
    - require:
      - Relocate core dump to /var/crash

update /etc/kdump.conf:
  file.line:
    - name: /etc/kdump.conf
    - content: "core_collector makedumpfile -c --message-level 1 -d 31"
    - match: "core_collector makedumpfile -l --message-level 1 -d 31"
    - mode: "replace"

cron job for coredumps rotation:
  file.managed:
    - name: /etc/cron.daily/coredumps_rotate
    - contents: |
        #!/bin/sh
        ls -t /var/crash/core-* | tail -n +60 | xargs rm -f
        EXITVALUE=$?
        if [ $EXITVALUE != 0 ]; then
            /usr/bin/logger -t coredumps "ALERT coredumps rotation exited abnormally with [$EXITVALUE]"
        fi
        exit 0
    - create: True
    - makedirs: True
    - replace: False
    - user: root
    - group: root
    - dir_mode: 755
    - mode: 0700
