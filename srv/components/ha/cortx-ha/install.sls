include:
  - components.ha.cortx-ha.prepare

Install cortx-ha:
  pkg.installed:
    - name: cortx-ha
    - require:
      - Add cortx-ha yum repo
