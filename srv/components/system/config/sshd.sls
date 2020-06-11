Set ClientAliveInterval:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^ClientAliveInterval .*
    - repl: ClientAliveInterval 60
    - append_if_not_found: True

Set ClientAliveCountMax:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^ClientAliveCountMax .*
    - repl: ClientAliveCountMax 10000
    - append_if_not_found: True

Set SSH port:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^TCPKeepAlive .*
    - repl: TCPKeepAlive yes
    - append_if_not_found: True

Restart sshd service:
  service.running:
    - name: sshd
    - enable: True
    - reload: True
    - listen:
      - file: /etc/ssh/sshd_config

Comment default wheel conf:
  file.comment:
    - name: /etc/sudoers
    - regex: ^\%wheel.*ALL=\(ALL\).*ALL$
    - char: '#'

Set NOPASSWD for wheel:
  file.append:
    - name: /etc/sudoers
    - text:
      - "\n## Allows people in group wheel to run all commands without a password"
      - "%wheel        ALL=(ALL)       NOPASSWD: ALL"
