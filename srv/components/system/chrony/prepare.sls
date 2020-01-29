#Check time server port access:
#  firewall.check:
#    - name: "{{ pillar['system']['ntp']['time_server'] }}"
#    - port: 123
#    - proto: 'udp'