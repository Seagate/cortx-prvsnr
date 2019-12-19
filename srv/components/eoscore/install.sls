Install Lustre:
  pkg.installed:
    - pkgs:
      - kmod-lustre-client: latest
      - lustre-client: latest
      # - lustre-client-devel
    - refresh: True

Install EOSCore:
  pkg.installed:
    - pkgs:
      - mero: latest
      # - mero-debuginfo
    - refresh: True
