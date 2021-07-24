#!/bin/bash
set -eu

echo "Finding the multipath devices to be used for storage config commands"

cp /usr/share/doc/device-mapper-multipath-0.4.9/multipath.conf /etc/multipath.conf
systemctl restart multipathd
sleep 5

tot_mpath_dev_cnt=$(multipath -ll|grep mpath|sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g'|wc -l)
cvg0_dev_cnt=$(( tot_mpath_dev_cnt/2 ))
cvg0_mpaths=$(multipath -ll|grep mpath|sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g' | head -n $cvg0_dev_cnt|paste -s -d, -)
md_devs_cvg0=$(echo ${cvg0_mpaths%%,*})
data_devs_cvg0=$(echo ${cvg0_mpaths#*,})

cvg1_dev_cnt=$(( tot_mpath_dev_cnt/2 ))
cvg1_mpaths=$(multipath -ll|grep mpath|sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g' | tail -n $cvg1_dev_cnt|paste -s -d, -)
md_devs_cvg1=$(echo ${cvg1_mpaths%%,*})
data_devs_cvg1=$(echo ${cvg1_mpaths#*,})

echo -e "CVG Devices:
-----------cvg0-------------
data_devices: $md_devs_cvg0
metadata_devices: $data_devs_cvg0

-----------cvg1--------------
data_devices: $md_devs_cvg1
metadata_devices: $data_devs_cvg1

Commands parameters to be used:

-----------CLI parameters for cvg0--------------
--cvg 0 --data_devices $data_devs_cvg0 --metadata_devices $md_devs_cvg0

-----------CLI parameters for cvg1--------------
--cvg 1 --data_devices $data_devs_cvg1 --metadata_devices $md_devs_cvg1