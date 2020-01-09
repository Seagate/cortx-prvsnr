## Python API:
Defines python api's for deploying the EOS components on host system. It uses saltstack python API to apply salt states from python api's.

### Python API for NTP update:

### ntp.py
Defines a python API to update NTP using below functions:
- update_pillar: 
    - Updates pillar data defined in /opt/seagate/eos-prvsnr/pillar/components/system.sls using Pillar class.
- refresh_ntpd: 
    - Restarts the ntpd service once the configuration file is updated.

### pillar.py
Defines pillar class to update the pillar data as per user inputs using below functions:
- __load_defaults:
    - Parse the default pillar document in a stream
- __backup_pillar:
    - Backup existing pillar document
- __save:
    - Updates the pillar document as per user input 

### How to use:
1. Set sys path to import python modules in different directories
    ```
    export PYTHONPATH=${PYTHONPATH}:/opt/seagate/eos-prvsnr/api/python/ 
    ```
2. Import any module from utils:
    ```
     from utils import pillar
    ```
3.  How to use:
    ```
    python3 ntp.py

    OR

    pyhton3 ntp.py '{ "time_server": "TIME-SERVER-IP", "timezone": "TIMEZONE" }'
    ```
