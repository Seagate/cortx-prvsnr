Update /etc/hosts:
  file.managed:
    - name: /etc/hosts
    - content:
      - {{ salt['pillar.get']('s3client:s3server:ip', '127.0.0.1') }}  seagatebucket.s3.seagate.com seagate-bucket.s3.seagate.com
       seagatebucket123.s3.seagate.com seagate.bucket.s3.seagate.com
      - {{ salt['pillar.get']('s3client:s3server:ip', '127.0.0.1') }}  s3-us-west-2.seagate.com seagatebucket.s3-us-west-2.seagate.com
      - {{ salt['pillar.get']('s3client:s3server:ip', '127.0.0.1') }}  iam.seagate.com sts.seagate.com s3.seagate.com
      - mode: ensure
      - before: 127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4

Setup driver file:
  file.managed:
    - name: /opt/cos/conf/driver.conf
    - create: True
    - contents:
      - [driver]
      - name=DriverA
      - url=http://{{grains['ip_interfaces']['data0'][0]}}:18088/driver

Setup controller file:
  file.managed:
    - name: /opt/cos/conf/controller.conf
    - create: True
    - contents:
      - [controller]
      - concurrency = 2
      - drivers = 2
      - log_level = INFO
      - log_file = log/system.log
      - archive_dir = archive
      -
      - [driver1]
      - name = DriverA
      - url = http://{{grains['ip_interfaces']['data0'][0]}}:18088/driver

Copy sample file:
  file.managed:
    - name: /opt/cos/conf/s3-config-sample.xml
    - source: salt://components/performance_testing/cosbench/files/conf/s3-config-sample.xml
    - template: jinja

Open driver port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 18088
    - connstate: NEW
    - family: ipv4
    - save: True

Open controller port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 19088
    - family: ipv4
    - save: True

Open http port for s3server:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 80
    - family: ipv4
    - save: True

Open https port for s3server:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 443
    - family: ipv4
    - save: True

Change driver start file permissions:
  file.managed:
    - name: /opt/cos/start-driver.sh
    - mode: 755

Change controller start file permissions:
  file.managed:
    - name: /opt/cos/start-controller.sh
    - mode: 755

Change driver stop file permissions:
  file.managed:
    - name: /opt/cos/stop-driver.sh
    - mode: 755

Change controller stop file permissions:
  file.managed:
    - name: /opt/cos/stop-controller.sh
    - mode: 755

Start driver:
  cmd.run:
    - name: /opt/cos/start-driver.sh
    - cwd: /opt/cos
    - onlyif: test -x /opt/cos/start-driver.sh

Start controller:
  cmd.run:
    - name: /opt/cos/start-controller.sh
    - cwd: /opt/cos
    - onlyif: test -x /opt/cos/start-controller.sh
