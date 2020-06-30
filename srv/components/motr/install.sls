Install Motr:
  pkg.installed:
    - pkgs:
      - cortx-motr: latest
      # - mero-debuginfo
    - refresh: True
