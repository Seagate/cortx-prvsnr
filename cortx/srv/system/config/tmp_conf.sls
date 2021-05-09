Configure temp.conf:
  file.blockreplace:
    - name: /usr/lib/tmpfiles.d/tmp.conf
    - backup: False
    - append_if_not_found: True
    - content: |
        x /tmp/csm
        x /tmp/hotfix
        x /tmp/csm_web
        x /tmp/support_bundle
