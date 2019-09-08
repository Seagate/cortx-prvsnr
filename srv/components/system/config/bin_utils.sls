Copy ipmi utilities:
  file.recurse:
    - name: /bin
    - source: salt://components/system/files/bin
    - keep_source: False
    - dir_mode: 0755
    - file_mode: 0755
    - replace: True
    - maxdepth: 0
