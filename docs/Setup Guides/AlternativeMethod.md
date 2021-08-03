# Alternative method for removing LVM metadata information from enclosure volumes

As outlined in [Known Issue #18](https://github.com/Saumya-Sunder/cortx-prvsnr-1/blob/patch-1/docs/Setup%20Guides/KnownIssues.md#manual-fix-in-case-the-node-has-been-reimaged), you may run into a problem during the reinstall with LVM metadata present on the enclosure volumes.

If the original method of removing the LVM metadata fails, you could try an alternative approach:

1. Log in to the host

2. Run `partprobe`

3. Run `lsblk`

You are looking for something like this in the output:

```
sdab                                     65:176  0  58.1T  0 disk`
├─sdab1                                  65:177  0 931.3G  0 part`
├─sdab2                                  65:178  0  57.2T  0 part`
└─mpathb                                253:17   0  58.1T  0 mpath`
  ├─mpathb1                             253:22   0 931.3G  0 part`
  └─mpathb2                             253:23   0  57.2T  0 part`
```

Note the size of `mpathb1` and `mpathb2` - these are the partitions on the enclosure.

Alternatively, you can see something like this:

```
sdg                                       8:96   0  58.1T  0 disk
└─sdg2                                    8:98   0  57.2T  0 part
  └─vg_metadata_srvnode--1-lv_main_swap 253:1    0  29.2T  0 lvm
--
sdk                                       8:160  0  58.1T  0 disk
└─sdk2                                    8:162  0  57.2T  0 part
  └─vg_metadata_srvnode--2-lv_main_swap 253:2    0  29.2T  0 lvm
```

These are formatted (as linux-swap) partitions.

You could also see both variations in the output. 

4. If you see `mpath*` devices with partitions, run the following command:

```
pvremove -ffy /dev/mapper/mpathX2
```

This will destroy metadata for LVM's physical volume.

5. If you are here for [Known Issue #20](https://github.com/Saumya-Sunder/cortx-prvsnr-1/blob/patch-1/docs/Setup%20Guides/KnownIssues.md#problem) then also run the following command:

```
wipefs -a /dev/disk/by-id/dm-name-mpathX2
```

6. Overwrite the first 255 blocks on both partitions. Run:

```
dd if=/dev/zero of=/dev/mapper/mpathX2 bs=512 count=255
dd if=/dev/zero of=/dev/mapper/mpathX1 bs=512 count=255
dd if=/dev/zero of=/dev/mapper/mpathX bs=512 count=255
```

7. Kill the partitions. Run:

```
parted -s /dev/mapper/mpathX rm 2
parted -s /dev/mapper/mpathX rm 1
parted -s /dev/mapper/mpathX mklabel gpt
```

8. If you only see the second variation (i.e., there are no mpath devices, only swap devices are present). For each `"swap"` device run:

```
dd if=/dev/zero of=/dev/sdX2 bs=512 count=255
dd if=/dev/zero of=/dev/sdX1 bs=512 count=255
dd if=/dev/zero of=/dev/sdX bs=512 count=255
```

9. Destroy the partitions. Run (for each `"swap"` device):

```
parted -s /dev/sdX mklabel gpt
```

Note: You will likely see the message like this:

```
Error: Partition(s) 2 on /dev/sdj have been written, but we have been unable to inform the kernel of the change, 
probably because it/they are in use.  As a result, the old partition(s) will remain in use.  
You should reboot now before making further changes.
```

It's ok to ignore this message. 

Proceed with the re-install.

Note: It's ok to perform steps 7-8 even if you performed steps 4-6.


**If you really want to confirm that partitions are gone**

10. Edit the following files:

```
/boot/efi/EFI/redhat/grub.cfg 
/boot/efi2/EFI/redhat/grub.cfg
```

11. Search for the word `"metadata"` (it should appear 4 times)

12. Completely remove the following portion of the lines (total in 2 places):

```
rd.lvm.lv=vg_metadata_srvnode-1/lv_main_swap rd.lvm.lv=vg_metadata_srvnode-2/lv_main_swap
```

(hint: it's total of 90 symbols starting from `"r"` in `"rd.lvm.lv=vg_metadata_srvnode-1"`)

13. Save both files and reboot the server. 

14. Repeat steps 1-3 and check for the presence of the partitions.
