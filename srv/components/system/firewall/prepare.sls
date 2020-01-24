#To enable firewall IP table has to be disabled
Disable iptables:
  service.dead:
    - name: iptables
    - enable: False

Disable ip6tables:
  service.dead:
    - name: ip6tables
    - enable: False

Disable ebtables:
  service.dead:
    - name: ebtables
    - enable: False

# Mask the above to ensure they are never started
Mask iptables:
  service.masked:
    - name: iptables

Mask ip6tables:
  service.masked:
    - name: ip6tables

Mask ebtables:
  service.masked:
    - name: ebtables

# Enable Firewalld
Unmask Firewall service:
  service.unmasked:
    - name: firewalld

Start and enable Firewall service:
  service.running:
    - name: firewalld
    - enable: True
