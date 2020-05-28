import re
from subprocess import PIPE, Popen

def _run_shell(cmd):
  process = Popen(cmd,stdin=PIPE,stdout=PIPE,stderr=PIPE,encoding='utf8')
  out,err = process.communicate()
  return (out,err,process.returncode)


def bmc_ip(grains):
  cmd = "ipmitool lan print 1"
  if "physical" in grains['virtual']:
    out,err,ret = _run_shell(cmd.split())
    if ret:
      raise Exception(err)
    ip = re.search(".*?IP Address\s*\:\s(.*)",out).group(1)
    if ip:
      return {'bmc_ip': ip}
  return {'bmc_ip': None}

def is_primary():
  cmd = "systemctl status salt-master"
  out,err,ret = _run_shell(cmd.split())
  if err:
    raise Exception(err)
  else:
    if ret:
      return {'is_primary': False}
  return {'is_primary': True}

