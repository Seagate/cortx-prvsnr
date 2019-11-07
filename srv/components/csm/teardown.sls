Remove csm package:
  pkg.purged:
    - pkgs:
      - eos_csm

Remove nodejs:
  file.absent:
    - name: /opt/nodejs

Reset bash_profile:
  file.blockreplace:
    - name: ~/.bash_profile
    - marker_start: '# DO NOT EDIT: Nodejs'
    - marker_end: '# DO NOT EDIT: End'
    - content: ''
