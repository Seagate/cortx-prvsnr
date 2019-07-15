Install Lustre:
  pkg.installed:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel

Install EOSCore:
  pkg.installed:
    - pkgs:
      - mero
      # - mero-debuginfo
