Remove nodejs:
  file.absent:
    - name: /opt/nodejs

Remove nodejs from bash_profile:
  file.replace:
    - name: ~/.bashrc
    - pattern: "# DO NOT EDIT: Nodejs binaries.*?# DO NOT EDIT: End"
    - flags: ['MULTILINE', 'DOTALL']
    - repl: ''
    - ignore_if_missing: True

Source bash_profile for nodejs cleanup:
  cmd.run:
    - name: source ~/.bashrc
