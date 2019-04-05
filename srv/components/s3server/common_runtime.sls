{% import_yaml 'components/install/defaults.yaml' as defaults %}
{% set rpm_build_dir = defaults.tmp_dir + "rpmbuild/RPMS/x86_64" %}

install_common_runtime:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - openssl
      - openssl-libs
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog
      - openldap-servers
    - require:
      - remove_pkgs

Update to latest selinux-policy (required by latest openldap):
  pkg.latest:
    - name: selinux-policy

Enable http port in selinux:
  cmd.run:
    - name: setsebool httpd_can_network_connect on -P
    - onlyif: salt['grains.get']('selinux:enabled')

Install haproxy:
  pkg.installed:
    - name: haproxy

Setup haproxy config:
  file.managed:
    - name: /etc/haproxy/haproxy.cfg
    - source: salt://components/install/s3server/files/haproxy/haproxy.cfg
    - require:
      - pkg: Install haproxy

Setup haproxy 503 error code to http file:
  file.managed:
    - name: /etc/haproxy/errors/
    - source: salt://components/install/s3server/files/haproxy/503.http

Setup haproxy config to enable logs:
  file.managed:
    - name: /etc/rsyslog.d/haproxy.conf
    - source: salt://components/install/s3server/files/haproxy/rsyslog.d/haproxy.conf
    - watch_in:
      - service: rsyslog

service_rsyslog:
  service.running:
    - name: rsyslog
    - enable: true

Install keepalived:
  pkg.installed:
    - name: keepalived

Setup keepalived master config (sample, manually updated):
  file.managed:
    - name: /etc/keepalived/keepalived.conf.master
    - source: salt://components/install/s3server/files/keepalived/keepalived.conf.master

Create working directory for S3 server:
  file.directory:
    - name: /var/seagate/s3
    - makedirs: True
