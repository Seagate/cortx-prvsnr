Install eos-sspl packages:
  pkg.installed:
    - name: eos-sspl
    - version: latest
    - refresh: True

Install flask:
  pip.installed:
    - name: flask
    - version: 1.1.1

Install eos-sspl-test:
  pkg.installed:
    - name: eos-sspl-test
    - requires:
      - Install flask
