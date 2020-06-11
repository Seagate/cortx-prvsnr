include:
  - .prepare

Install cortx-sspl packages:
  pkg.installed:
    - name: cortx-sspl
    - version: latest
    - refresh: True
    - require:
      - Add sspl yum repo

Install flask:
  pip.installed:
    - name: flask
    - version: 1.1.1

Install cortx-sspl-test:
  pkg.installed:
    - name: cortx-sspl-test
    - requires:
      - Install flask
      - Install eos-sspl packages
