Remove nodejs:
  file.absent:
    - name: /opt/nodejs

Remove nodejs from bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Nodejs binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: ''

Source bash_profile for nodejs cleanup:
  cmd.run:
    - name: source ~/.bashrc
