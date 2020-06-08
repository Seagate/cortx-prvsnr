# TODO TEST OES-8473

ssh_dir_created:
  file.directory:
    - name: /root/.ssh
    - mode: 700

ssh_priv_key_deployed:
  file.managed:
    - name: /root/.ssh/id_rsa_prvsnr
    - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
    - show_changes: False
    - keep_source: True
    - mode: 600
    - requires:
      - ssh_dir_created

ssh_pub_key_deployed:
  file.managed:
    - name: /root/.ssh/id_rsa_prvsnr.pub
    - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
    - keep_source: True
    - mode: 600
    - requires:
      - ssh_dir_created

ssh_key_authorized:
  ssh_auth.present:
    - source: /root/.ssh/id_rsa_prvsnr.pub
    - user: root
    - requires:
      - ssh_pub_key_deployed

ssh_config_updated:
  file.managed:
    - name: /root/.ssh/config
    - source: salt://ssh/files/config
    - keep_source: True
    - mode: 600
    - template: jinja
