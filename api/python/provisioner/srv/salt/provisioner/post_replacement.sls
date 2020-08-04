Set replacement flag:
  file.managed:
    - name: /etc/profile.d/set_replacement_env.sh
    - contents: |
        #!/bin/bash
        test ${REPLACEMENT_NODE} || export REPLACEMENT_NODE=true
    - create: true

Apply changes:
  cmd.run:
    - name: 'source /etc/profile.d/set_replacement_env.sh'
    - require:
      - Set replacement flag