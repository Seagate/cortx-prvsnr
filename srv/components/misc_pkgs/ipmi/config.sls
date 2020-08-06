# TODO TEST CORTX-8473

bmc_ip_is_set:
  cmd.script:
    - source: salt://components/misc_pkgs/ipmi/files/bmc.sh
    - args: "{{ grains.id }} 2"
