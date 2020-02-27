# include:
#   - components.system.firewall.prepare
#   - components.system.firewall.config
#   - components.system.firewall.sanity_check

Disable firewall:
  service.dead:
    - name: firewalld
    - enable: false
