# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call lyveutil.decrypt "secret" "component"
from eos.utils.security.cipher import Cipher
from salt import client

def decrypt(secret =None, component=None):
  """ Decrypt secret.

  Args:
    secret: Secret to be decrypted.
  """
  retval = None
  cluster_id = __grains__['cluster_id']
  cipher_key = Cipher.generate_key(cluster_id, component)

  if secret:
    retval = Cipher.decrypt(cipher_key, secret.encode("utf-8"))
  return retval.decode("utf-8")
