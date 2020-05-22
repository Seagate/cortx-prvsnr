Create /var/log/journal to store logs:
  file.directory:
    - name: /var/log/journal
    - makedirs: True

Create systemd-tempfile:
  cmd.run:
    - name: systemd-tmpfiles --create --prefix /var/log/journal

Update journald configuration:
  file.append:
    - name: /etc/systemd/journald.conf
    - text: |
        Storage=persistent

Restart systemd-journald:
  module.run:
    - service.restart:
      - systemd-journald
