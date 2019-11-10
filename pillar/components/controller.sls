storage_mc:
  name: Gallium-NX3-m06   # equivalent to fqdn for server node
  #metadata_vols:

  virtual_volumes:
    poolA:
      type: virtual #virtual or lenear
      disks_range: 0.0-41
      nvols: 8
      size: 10TB
      mappings: 
        map_vols: no  #yes/no 
        host_initiator1:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
        host_initiator2:
          id: #0x21000024ff6c505d # initiator id 
          access_mode: rw  #options: ro, rw, na
    poolB:
      type: virtual #virtual or lenear
      disks_range: 0.0-41
      nvols: 8
      size: 10TB
      mappings: 
        map_vols: no
        host_initiator1:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
        host_initiator2:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
