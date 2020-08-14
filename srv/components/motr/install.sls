Install Motr:
  pkg.installed:
    - pkgs:
      - cortx-motr: latest
      # - motr-debuginfo
    - refresh: True
