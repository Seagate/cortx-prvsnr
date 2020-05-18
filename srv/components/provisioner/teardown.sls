Delete rsyslog provisioner conf:
  file.absent:
    - name: /etc/rsyslog.d/prvsnrfwd.conf

Delete old rsyslog provisioner conf:
  file.absent:
    - name: /etc/rsyslog.d/2-prvsnrfwd.conf