create_volumes()
{
    _count=$1
    _size=$2
    _baselun=$3
    _basename=$4
    _ports=$5
    _pool=$6
    _cmd="create volume-set access rw baselun $_baselun basename $_basename count $_count pool $_pool size $_size ports $_ports"
    echo "Creating volume set with $_count volumes of size $_size in pool $_pool and mapped to ports $_ports"
    cmd_run $_cmd
}