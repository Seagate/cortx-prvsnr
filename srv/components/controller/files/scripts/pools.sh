add_disk_group()
{
    _dg=$1
    _disks_range=$2
    _pool=$3
    _cmd="add disk-group type virtual disks $disks_range level adapt pool $_pool $_dg"
    echo "Creating disk group $_dg with $_disks_range disks"
    cmd_run $_cmd
}
