# This file is dummy file to test working of a custom module in general.

def test():
  print("Test module")
  print(__pillar__['sspl'])
  print(type(__pillar__))
  return True
