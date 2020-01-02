stop service sspl-ll:
  service.dead:
    - name: sspl-ll

stop service rabbitmq-server:
  service.dead:
    - name: rabbitmq-server

Remove sspl packages:
  pkg.purged:
    - pkgs:
      - sspl
      - libsspl_sec-method_none
      - libsspl_sec
      - rabbitmq-server

Remove file sspl_ll.conf:
  file.absent:
    - name: /etc/sspl.conf

Remove file sspl_ll.conf.bak :
  file.absent:
    - name: /etc/sspl.conf.bak

Remove directory install sspl-ll:
  file.absent:
    - name: /etc/sspl-ll

Remove directory install sspl:
  file.absent:
    - name: /opt/seagate/sspl

Remove rabbitmq log dir:
  file.absent:
    - name: /var/log/rabbitmq

Remove user sspl-ll:
  user.absent:
    - name: sspl-ll
    - purge: True
    - force: True

Remove user rabbitmq:
  user.absent:
    - name: rabbitmq
    - purge: True
    - force: True

# Remove test fw lettuce:
#   pip.removed:
#     - name: lettuce
#     - bin_env: '/usr/bin/pip'

Remove sspl-ll sudoers file:
  file.line:
    - name: /etc/sudoers
    - mode: delete
    - match: "sspl-ll ALL = NOPASSWD: /usr/sbin/smartctl, /usr/sbin/mdadm, /usr/bin/mount, /uss
r/bin/umount, /usr/sbin/swapon, /usr/sbin/swapoff, /usr/sbin/hdparm, /usr/bin/syy
stemctl, /usr/sbin/wbcli"
