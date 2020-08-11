Install corosync:
  pkg.installed:
    - name: corosync

Install pacemaker:
  pkg.installed:
    - name: pacemaker
      
Install pcs:
  pkg.installed:
    - name: pcs

Install fence-agents-ipmilan:
  pkg.installed:
    - name: fence-agents-ipmilan    # For fencing
