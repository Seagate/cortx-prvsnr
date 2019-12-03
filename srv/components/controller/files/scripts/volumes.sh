create_volumes()
{
    # Sample command to create a volume set
    # create volume-set access rw baselun 0 basename dg01- count 8 pool a size 30T ports A0-A3,B0-B3'
    _baselun=$1
    _basename=$2
    _count=$3
    _pool=$4
    _size=$5
    _ports=$6
    _cmd="create volume-set access rw baselun $_baselun basename $_basename count $_count pool $_pool size $_size ports $_ports"
    echo "Creating volume set with $_count volumes of size $_size in pool $_pool and mapped to ports $_ports"
    cmd_run $_cmd
}