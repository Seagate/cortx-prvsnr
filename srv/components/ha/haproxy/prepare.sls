{% if grains['selinux']['enabled'] and 'enforcing' in grains['selinux']['enforced'].lower() %}
Set selinux bool for httpd:
  selinux.boolean:
    - name: httpd_can_network_connect
    - value: true
    - persist: True

Set selinux bool for haproxy:
  selinux.boolean:
    - name: haproxy_connect_any
    - value: 1
    - persist: True
{% endif %}

Clean existing logrotate configuration:
  file.absent:
    - name: /etc/cron.daily/logrotate

Add haproxy user to certs group:
  group.present:
    - name: certs
    - addusers:
      - haproxy

