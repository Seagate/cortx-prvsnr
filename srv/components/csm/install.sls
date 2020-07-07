Install csm package:
  pkg.installed:
    - pkgs:
      - cortx-csm_agent: latest
      - cortx-csm_web: latest
    - refresh: True
