install_halon:
  pkg.installed:
    - pkgs:
      - halon
    - refresh: True
    - require:
      - pkgrepo: add_halon_repo
