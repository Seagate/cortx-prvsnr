base:
  '*':
    - ignore_missing: True
    - groups.all.*                     # user all minions vars
  {{ grains.id }}:
    - ignore_missing: True
    - minions.{{ grains.id }}.*             # default per-minion vars
