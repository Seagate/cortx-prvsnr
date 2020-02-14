# Fail provisioning if this check returns non-zero
#Check system hostname:
#  cmd.run:
#    - name: test $(salt --no-color eosnode-1 grains.get host|tail -1|tr -d "[:blank:]") == $(hostname)
