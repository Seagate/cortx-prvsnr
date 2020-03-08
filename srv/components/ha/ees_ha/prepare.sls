<<<<<<< HEAD
<<<<<<< HEAD
=======
include:
  - components.hare.prepare

>>>>>>> EOS-5962: Direct network config.
=======
>>>>>>> M2: run ees_ha component in deploy_eos by default
Render ha input params template:
  file.managed:
    - name: /var/lib/hare/build-ees-ha-args.yaml
    - source: salt://components/ha/ees_ha/files/ha-params.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
