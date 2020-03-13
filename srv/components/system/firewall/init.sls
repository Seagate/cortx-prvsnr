include:
  - components.system.firewall.install
  - components.system.firewall.prepare
  - components.system.firewall.config
  - components.system.firewall.sanity_check

# Disable Firewall:
#   service.dead:
#     - name: firewalld
#     - enable: false
