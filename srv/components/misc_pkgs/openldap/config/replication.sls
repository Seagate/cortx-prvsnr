# Open port389 for slapd:
#   iptables.insert:
#     - position: 1
#     - table: filter
#     - chain: INPUT
#     - jump: ACCEPT
#     - protocol: tcp
#     - match: tcp
#     - dport: 389
#     - family: ipv4
#     - save: True

# Open port636 for slapd:
#   iptables.insert:
#     - position: 1
#     - table: filter
#     - chain: INPUT
#     - jump: ACCEPT
#     - protocol: tcp
#     - match: tcp
#     - dport: 636
#     - family: ipv4
#     - save: True

Configure openldap syncprov_mod:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/eos-prvsnr/generated_configs/ldap/syncprov_mod.ldif

Configure openldap syncprov:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/eos-prvsnr/generated_configs/ldap/syncprov.ldif
    - require:
      - Configure openldap syncprov_mod 

Configure openldap replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/eos-prvsnr/generated_configs/ldap/replicate.ldif
    - watch_in:
      - service: Restart Slapd
    - require:
      - Configure openldap syncprov

Restart Slapd:
  service.running:
    - name: slapd
    - full_restart: True

