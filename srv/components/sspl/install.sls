Install sspl packages:
  pkg.installed:
    - name: sspl
    - version: latest
    - refresh: True

Install flask:
  pip.installed:
    - name: flask
    - version: 1.1.1

Install sspl-test:
  pkg.installed:
    - name: sspl-test
