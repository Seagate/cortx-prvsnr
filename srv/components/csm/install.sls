Install csm package:
  pkg.installed:
    - pkgs:
      - eos-csm_agent: latest
      - eos-csm_web: latest
    - refresh: True
