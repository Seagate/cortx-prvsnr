Start CSM agent:
  service.running:
    - name: csm_agent
    - enable: True

Start CSM web:
  service.running:
    - name: csm_web
    - enable: True
