
cleanup_provisioning()
{
    cmd_run 'show volumes'
    cmd_run 'delete volumes volume-0'
    cmd_run 'show disk-groups'
    cmd_run 'delete pools 1 prompt yes' 
}