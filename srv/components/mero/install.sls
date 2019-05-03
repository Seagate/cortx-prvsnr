install_lustre:
  pkg.installed:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel

install_mero:
  pkg.installed:
    - pkgs:
      - mero
      # - mero-debuginfo
