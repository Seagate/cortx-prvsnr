#include:
#  - .prepare

Install eos-sspl packages:
  pkg.installed:
    - name: eos-sspl
    - version: latest
    - refresh: True
    # - require:
    #   - Add sspl yum repo

Install flask:
  pip.installed:
    - name: flask
    - version: 1.1.1

Install eos-sspl-test:
  pkg.installed:
    - name: eos-sspl-test
    - version: latest
    - require:
      - Install flask
      - Install eos-sspl packages
