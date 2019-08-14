Clean existing logrotate configuration:
  file.absent:
    - name: /etc/cron.daily/logrotate
