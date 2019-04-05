import os,sys,re
from collections import defaultdict
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 ai

def by_device():
    '''
    Retrieve candidate block devices for raid configurations

    CLI Example:

    .. code block:: bash
    salt '*' stx_disk.by_device
    '''
    block_device_list={}
    block_path = '/sys/class/block/'
    disk_regex = re.compile('^sd.*[^\d]$')
    for disk in os.listdir(block_path):
        if re.match(disk_regex, disk):
            f = open(block_path + disk + '/device/model', "r")
            model = f.read().strip(' \t\n\r')
            f.close
            f = open(block_path + disk + '/device/vendor', "r")
            vendor = f.read().strip(' \t\n\r')
            f.close
            f = open(block_path + disk + '/size', "r")
            size = f.read().strip(' \t\n\r')
            f.close
           # print block_path
            block_device_list[disk] = {
                'model': model,
                'vendor': vendor,
                'size': ((int(size)/2)/(1024*1024))
            }
    return block_device_list

def by_model():
    '''
    Maps maps disk models found to arrays of devices attached.

    CLI Example:

    .. code block:: bash
    salt '*' stx_disk.by_model
    '''
    models = defaultdict(list)
    for dev,value in by_device().iteritems():
        models[value["model"]].append(dev)
    return models

def by_vendor():
    '''
    Maps disk device vendor found to arrays of devices attached.

    CLI Example:

    .. code block:: bash
    salt '*' stx_disk.by_vendor
    '''
    vendors = defaultdict(list)
    for dev,value in by_device().iteritems():
        vendors[value["vendor"]].append(dev)
    return vendors

def by_size():
    '''
    Maps disk sizes found to arrays of devices attached.

    CLI Example:

    .. code block:: bash
    salt '*' stx_disk.by_vendor
    '''
    vendors = defaultdict(list)
    for dev,value in by_device().iteritems():
        vendors[value["size"]].append(dev)
    return vendors

def by_criteria(min_gb = 0, max_gb=-1, model_substr=str(""), vendor_substr=str("")):
    '''
    Returns an array of disk devices matching criteria
    CLI Example:

    ... code block:: bash
    salt '*' stx_disk.by_criteria (100, 150, '', 'Sandisk')
    salt '10*' saltutil.sync_all && salt '10*' stx_disk.by_criteria 100 '150' "SanDisk" "ATA"
    '''
    min_gb = int(min_gb)
    max_gb = int(max_gb)
    matched = []
    rejected = []
    print 'min=', min_gb
    print 'max=', max_gb
    for dev,value in by_device().iteritems():
        match = False;
        this_size = value['size']
        this_model = str(value['model'])
        this_vendor = str(value['vendor'])
#        print "this model :",this_model
#        print "this vendor:",this_vendor
#        print "this size  :",this_size
#        print "this dev   :", dev
        if max_gb > -1 and this_size > max_gb:
#            print "Skipping due to max size"
            rejected.append(dev)
            continue
        if this_size < min_gb:
#            print "Skipping due to min size:", dev
            rejected.append(dev)
            continue
        if len(model_substr) > 0:
#            print "Checking model string match"
            if 0 > this_model.find(model_substr):
                print "Skipping due to model", model_substr, 'not found in', this_model, ' device:', dev
                rejected.append(dev)
                continue
        if len(vendor_substr) > 0:
#            print "Checking Vendor string match"
            if 0 > this_vendor.find(vendor_substr):
#                print "Skipping due to vendor", vendor_substr, 'not found in ', this_vendor, ' device:', dev
                rejected.append(dev)
                continue
#        print "Appending", dev
        matched.append(dev)
#        print 'matched:', dev
    ret={"matched": matched, "rejected": rejected}
    return ret
