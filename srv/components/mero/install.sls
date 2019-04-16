install_lustre:
  pkg.installed:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel
    - require:
      - pkgrepo: add_lustre_repo


install_mero:
  pkg.installed:
    - pkgs:
      - mero
      # - mero-debuginfo
    - require:
      - pkgrepo: add_mero_repo
      # - pkg: install_kernel
