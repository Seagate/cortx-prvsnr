# Protecting OS volumes / Emergency OS reinstallation in the field 

#### Current version: **0.4** 

## Table of Content
[Document history](#document-history)<br>
[User stories](#user-stories)<br>
[Problem statement](#problem-statement-and-notes)<br>
[Proposed changes:](#proposed-changes)<br>
- [Options](#options)
- [Phase-1: Initial Release](#phase-1-initial-release)
- [Phase-2: Future release (prior to GA)](#phase-2-future-release-prior-to-ga)
- [Storing core dump files](#storing-core-dump-files)<br>

[Emergency OS reinstallation in the field](#emergency-os-reinstallation-in-the-field)

<br>

### Document history:

| Revision | Revision date | Author | Description |
| -------- | :-----------: | ------ | --- |
| 0.1 | 2020-04-03 | Ivan Poddubnyy | Initial release |
| 0.2 | 2020-04-07 | Ivan Poddubnyy | Added/corrected information <br>about partitions’ structure in Phase-1 |
| 0.3 | 2020-04-10 | Ivan Poddubnyy | Expanded information about partition allocation |
| 0.4 | 2020-04-14 | Ivan Poddubnyy | Added section about storing core dump files |

 
## User stories

**User story:** As an admin, I need to ensure that I can always boot a CORTX appliance. 

**User story:** As a field support engineer, I need a simple way to replace and restore the entire server in the field. 

**User story:** As a field support engineer, I need a simple way to replace and restore failed server node in the field. 

**User story:** As a field support engineer, I need to ensure that I’m able to collect support bundle logs in a case of catastrophic server freeze. 

**User story:** As a developer, I need to ensure that my component is fully functional regardless of the partitions’ layout changes. 


## Problem statement and notes

The CORTX appliance uses two stand-alone servers, each connected to shared storage enclosure via two independent SAS links. The enclosure currently has 8 volumes, created on the single disk group. The volumes are accessible by both servers. Multipath priority is configured to ensure that each server has priority access to the “own” set of volumes. 

The servers boot from the local HDDs. 

The existing partitioning schema utilizes LVM and looks like this: 

| Device | Mount point | Size | FS type |
| --- | --- | --- | --- |
| `/dev/mapper/vg_sysvol-lv_root` | `/` | 200 GB | xfs |
| `/dev/sdag2` | `/boot` | 1 GB | xfs |
| `/dev/sdag1` | `/boot/efi` | 256 MB | vfat |
| `/dev/mapper/vg_sysvol-lv_tmp` | `/tmp` | 200 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_var` | `/var` | 200 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_log` | `/var/log` | 200 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_audit` | `/var/log/audit` | 128 MB | xfs |
| `/dev/mapper/vg_sysvol-lv_swap` | \<none\> | 100 GB | swap |

**Note:** Devices' names for ``/boot`` and ``/boot/efi`` could vary on different systems.

Unfortunately, by default, LVM does not protect against failed drives. This makes the system vulnerable to such events. 

It’s also difficult to perform a replacement of the server in the field, since the complete reinstall of the OS will be required as well as partial re-provisioning of the appliance. 

**Note:** Currently swap partition is located on a volume on the enclosure. We have to ensure that the swap size is at least 10% of Motr’s metadata size.  

 
## Proposed changes
### Options

There are several ways the limitation described above could be resolved:  

1. **_Option-1:_** We could utilize software RAID-1 configuration while leaving the OS partitions on the server. This way the appliance will be protected from a loss of single OS drive. The ability to collect and preserve the support bundle will remain intact. The swap location will remain as it is right now. 

	_Limitations of this option._ This option does not protect against the loss of both drives and/or the entire server. There are also complications related to OS recovery in the field, related to current inability to reinstall the OS in case of full server replacement.  

2. **_Option-2:_** We could move the entire OS to the enclosure. The servers will be switched to booting from a LUN located on the enclosure. The OS partitions will be protected against the loss of up to three drives using enclosure’s built-in mechanisms. In this case, swap space shall be migrated to use the local servers’ drives. This swap should be set to a higher priority. An additional swap space (in form of a swap file with a lower swap priority) should be created on the root partition (located on the enclosure). The secondary swap will be used in case the appliance runs out of RAM and primary swap space.  

	_Limitations of this option._ This option does not provide a clear way to collect support bundle in case of entire server freeze or replacement. The performance impact, while predicted to be minimal, is also unknown and shall be assessed before this solution is implemented. Also, in their current implementation, RAS mechanisms are relying on local access to IPMI and should be changed to use out of band approach. And the last but not least, this solution is completely dependent on the health of enclosure: its failure will make the system completely unusable, without any ability to collect logs or debug.  

3. **_Option-3:_** We could use a mixed approach and utilize both RAID-1 and moving OS partitions to the enclosure. With such approach, one half of the RAID-1 volume will be located on the server while another will be located on the enclosure. In case of the server failure, customers will be able to replace the server and boot from the part of the RAID, located on the enclosure. In case of the enclosure failure, ability to access the system and collect logs and debug the failure will remain, since the servers will remain accessible. The location of the swap space will change to use second HDD in the server (as primary swap space). The secondary swap space will remain on enclosure. 

	_Limitations of this approach._ Decrease of primary swap space seems to be the biggest change introduced by this solution. However, the actual impact, if any, needs to be determined. 

The **_Option-3_** seems to be the most logical way to improve our ability to recover from catastrophic server failures. However, with the current time we have for development (as of the date of initial version of this document), we cannot implement it to full extent. Thus, the implementation will be broken into two phases.  

**Conclusion:** Option #3 will be our implementation path forward. In order to achieve the final configuration, we’ll break it into two phases.  

  
### Phase-1: Initial Release

The initial release of CORTX software shall include the following changes: 

1. Add LVM’s RAID capability and configure both HDDs located in the servers to use software RAID-1 for all OS partitions. 

	Using separate RAID and LVM configuration won’t allow us to fully utilize all capabilities of LVM (in particular, the ability to resize LVM partitions on the fly). Thus, we have to use the LVM’s built-in support for software RAID. 

	* The RAID structure shall include two RAID volumes: 

| Name of the RAID volume | Purpose | Size | Is it resizable? |
| --- | --- |  --- | --- |
| ``/dev/md0`` | Contains `/boot` partition | 1 GB  | no |
| ``/dev/md1`` | Remaining OS partitions | 1 TB | **yes** |

* `/dev/md1` shall host LVM volume called `vg_sysvol`. The volume shall allocate the entire physical volume. 

**Note:** `/boot/efi` cannot be placed on the RAID volume due to UEFI limitations. We will create two separate partitions called `/boot/efi` and `/boot/efi2`, respectively. The partitions will be kept in sync using rsync run via crontab (once every 1 hr).

**Note:** The size of `/boot/efi` and `/boot/efi2` is 256 MB each. Filesystem type must be `vfat` (`fat32`). 

* The physical allocation of the drives for RAID-1 will be the following: 

| RAID device | Physical drive/volume (server) <br> (1st device) | Physical drive/volume (server) <br> (2nd device) |
| --- | --- | --- |
| `md0` | `/dev/sda2` | `/dev/sdb2` |
| `md1` | `/dev/sda3` | `/dev/sdb3` |

**Note:** The names of the devices could be different on different systems. The rule of thumb for identifying the devices used in phase-1 is that both devices are physically located on the server. 

* Partition structure will slightly change:

 | Device | RAID device | Mount point | Size | FS type |
| --- | --- | --- | --- | --- |
| `/dev/mapper/vg_sysvol-lv_root` | `md1` | `/` | 50 GB | xfs |
| `/dev/sdag2` | `md0` | `/boot` | 1 GB | xfs |
| `/dev/sdag1` | \<none\> | `/boot/efi` | 256 MB | vfat |
| `/dev/sdbg1` | \<none\> | `/boot/efi2` | 256 MB | vfat |
| `/dev/mapper/vg_sysvol-lv_tmp` | `md1` | `/tmp` | 20 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_var` | `md1` | `/var` | 40 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_log` | `md1` | `/var/log` | 500 GB | xfs |
| `/dev/mapper/vg_sysvol-lv_audit` | `md1` | `/var/log/audit` | 128 MB | xfs |
| `/dev/mapper/vg_sysvol-lv_swap` | \<none\> | 2 GB | swap |

**Note:** We will use UUIDs instead of partition names for `/boot`, `/boot/efi`, and `/boot/efi2`.

**Note:** Filesystem types shall not change. It’s based on the current RHEL/CentOS recommendations as well as general direction of the OS development. 

**Note:** Swap located on `/dev/mapper/vg_sysvol-lv_swap` partition should be given lowest priority (effectively excluded it from being used by the OS). <br><br>


2. Allocate and preserve the space on one of the enclosure volumes for future migration of RAID-1 to mixed setup. There are two possible ways this could be done: 

	* **_Option-1:_** Re-use the existing volume where swap and `/var/motr` is located. This will simplify and minimize the changes required for Provisioner. Swap space will be on the same volume; 

	* **_Option-2:_** Create new, smaller volume on the enclosure for OS partitions. The biggest problem with this approach is the size of the volume. We could predict the size of `/boot`, `/boot/efi`, `/var/log/audit`, and `/` partitions. However, it’s difficult to do that with `/var` and especially with `/var/log`. Moreover, this will complicate the Provisioner’s configuration. However, this may potentially make the layout more robust, especially if we decide to create a separate enclosure’s volume group (this idea, in its turn, has additional consequences: we’ll have to allocate additional disks to act as spares for this new group). 

	**Decision: Option-1** will be used in our configuration. 

	POC of the phase-1 design is available here: https://jts.seagate.com/browse/EOS-6779 


### Phase-2: Future release (prior to GA)
During one of the updates, a special script will be run to perform reconfiguration of the system in order to make it comply with the original design. 

The script shall perform the following actions: 

1. Create new partitions on the previously allocated space on enclosure’s volume (unless those partitions have been created already). This step could be done in parallel on both servers. 
2. Remove 2nd HDD from the LVM structure.
3. Disassemble the existing RAID-1 structure. 
4. Re-assemble RAID using the server and enclosure combination for the RAID volumes. 
5. Grow LVM volume to use the entire space of the RAID device (`md1`). 
6. Create new swap partition on the second HDD on the server and set its priority to highest.  

Steps 2-5 shall be done on one server at a time to minimize the risk to the entire system. Internal RAID mechanisms will start the synchronization process.  

Allocation of physical volumes for the RAID devices will change to the following: 

| RAID device | Physical drive/volume (server) <br> (1st device) | Physical drive/volume (enclosure) <br> (2nd device) |
| --- | --- | --- |
| `md0` | `/dev/sda2` | `/dev/disk/by-path/<SAS>-lunXp2` |
| `md1` | `/dev/sda3` | `/dev/disk/by-path/<SAS>-lunXp3` |

where:

* `\<SAS\>-lunX` is the first “local” volume on the enclosure (that is the volume with the higher priority – priority 50 – for the given server);
* `p2` and `p3` are respectively 2nd and 3rd partitions created on the enclosure’s volume. 

**Note:** The names of the devices could be different on different systems. The rule of thumb for identifying the devices used in phase-2 is that one of the devices is always physically located on the first disk on the server and the second device is always located on the first “local” volume on the enclosure. 

**Note:** `/boot/efi2` shall move to the enclosure as well. Its path will change from `/dev/sdb1` to `/dev/disk/by-path/<SAS>-lunXp1` (where `p1` is the first partition on the volume). 

**Note:** Secondary swap space shall be created on the remaining portion of the same enclosure’s volume where OS partitions (and `/var/motr`) will reside. The size of the swap space will be calculated based on the following formula: 

	2nd swap size = (size of the volume) - (total size of OS partitions) 

where the (total size of OS partitions) is roughly 1.2 TB (256 MB for `/boot/efi2`, 1 GB for `/boot`, and approximately 1 TB for the rest of the OS partitions). 

---

### Storing core dump files

**[ As of 2020-04-14 this section is under review and requires feedback before it can be implemented ]** 

Right now, S3server and Motr are storing their code dump files to `/var/motr`. This could lead to various issues such as the inability to unmount the partition in case code dump is in progress. 

To prevent this from happening, we may choose to do the following: 

1. Allocate dedicated partition for `/var/crash`: 
	* Estimated size of this partition should be at least 1 TB; 
	* The partition will not be mirrored; 
	* The partition will be located on the enclosure only; 
	* The partition will be under LVM control (in a separate PV and LV to avoid collision with the rest of the OS partitions); 
	* Note: there are two downsides of this: 
		* We are reserving more space on the enclosure for system-specific data (also that won't affect the size of the swap much in the long run); 
		* We may not be able to access core dumps if we lose access to the enclosure. 
2. Reconfigure S3server and Motr to save core dumps to `/var/crash/<component>` 
3. Enforce system-wide configuration to ensure all core files will go to `/var/crash` 
4. Reconfigure components (especially S3server and Motr) and turn off saving data from user buffers as part of a core dump. 

---



### Emergency OS reinstallation in the field
Even though the proposed RAID layout should protect the appliance from catastrophic server failures and simplify server's replacement in the field, there might be a need to reinstall the OS. At that time, depending on the customer’s environment and security restrictions, we may or may not be able to utilize external media (USB flash drives, CD/DVD/Blu-ray disks) that would contain the OS image.  

We may also may not be able to ship a fully pre-installed server to a particular customer.  

To avoid (or minimize) such problems, we should have an option to reinstall the OS in the field without dependency on the new server or the external media.  

**Note:** There’s no requirement to implement this option for the initial release. This is a desired solution and it can be introduced by one of the subsequent updates. However, we probably store the OS ISO on the appliance with the initial release to avoid dealing with it in the future.  

This challenge could be solved by utilizing PXE boot and kickstart setup. The following shall be considered while preparing this configuration: 

1. This option is emergency only. 
2. The cluster should be completely stopped at the time, HA and the services shutdown to avoid any unpredicted situation. 
3. Each server should have identical config and shall be able to re-install the partner node. 
4. The software image used for the reinstallation could be outdated and a software update of the reinstalled server will be necessary immediately after the installation.  
5. During reinstallation only the server should be reinstalled. That is, we shall not attempt to assembly the RAID but we shall create the partitions on server’s HDDs to be RAID-compatible. This way we can ensure that accidentally we don’t wipe off the data on the enclosure.  

**Note:** This also means that an extra, perhaps manual step will be require to complete assembly of the RAID. We should provide instructions to the user how to complete the process. 

6. The kickstart process should go over the directly connect link only, never go over the public management or data networks: 
	* Firewall shall be disabled for this operation. This is necessary to avoid unforeseen issues; 
	* DHCPd and TFTP/bootp services should be configured to listen/respond only on the direct connect interface; 
	* Web-server serving the kickstart image should be configured to respond only on the direct connect interface; 
	* The default state of the dhcpd, tftp/bootp, and web-server config for kickstart shall be “disabled”. The user will have to manually enable the required configuration (this can be done using a script that user will have to run to turn the necessary parameters on. The same script (with a different option) will have to be run to turn these configs off. Perhaps, this is an option for “Technical Access Portal” that can be used by trainer personnel only (e.g., Seagate support).  
