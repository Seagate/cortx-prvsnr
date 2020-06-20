Delete rsyslog provisioner conf:
  file.absent:
    - name: /etc/rsyslog.d/prvsnrfwd.conf

Delete old rsyslog provisioner conf:
  file.absent:
    - name: /etc/rsyslog.d/2-prvsnrfwd.conf

provisioner_package_installed:
  pkg.purged:
    - pkgs:
      - eos-prvsnr: latest

Delete provisioner yum repo:
  pkgrepo.absent:
    - name: {{ defaults.provisioner.repo.id }}
