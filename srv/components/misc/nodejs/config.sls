Set nodejs in bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Nodejs binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: 'export PATH=/opt/nodejs/node-v12.13.0-linux-x64/bin:$PATH'
    - append_if_not_found: True
    - append_newline: True
    - backup: False

Source bash_profile for consul addition:
  cmd.run:
    - name: source ~/.bashrc
