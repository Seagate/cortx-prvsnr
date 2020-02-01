Install ststsd utils:
  pkg.installed
    - name: stats_utils

Install csm package:
  pkg.installed:
    - name: eos_csm
    - version: latest
    - refresh: True
