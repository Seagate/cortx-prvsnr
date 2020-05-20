 # net-tools is required for ifconfig & netstat utilities.
 # ifconfig is required for LNet sanity test
 # netstat is required for s3 sanity to confirm opend ports

 Install net-tools for route command:
   pkg.installed:
     - name: net-tools
