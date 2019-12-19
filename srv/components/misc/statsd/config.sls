#Configure elasticsearch and statsd plugin:
#  cmd.run:
#    - names:
#      - wget https://drive.google.com/file/d/1DQ3kotbFcX9I8ef2MKA2-o2Ww7aQ0rEx/view?usp=sharing -P /opt/
#      - unzip /opt/statsd-utils*.zip
#      - mv /opt/statsd-utils-Dev-ajay-eduard /opt/statsd-utils


Update config:
  file.managed:
    - name: /etc/statsd/config.js
    - source: salt://components/misc/statsd/files/config.js
