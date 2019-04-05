# vi: set ft=ruby :

# Vagrantfile configuration fefernece:
#   https://www.vagrantup.com/docs/hyperv/configuration.html

# VM name
vm_name = 'ees-box'
# Maximum memory in MB
vm_memory = 2048
# Number of CPUs
vm_cpus = 2

# Disk configuration details
disks_dir = File.join(Dir.pwd, ".vdisks")
disk_count = 2         # number of disks
disk_size = 256         # in MB

Vagrant.configure("2") do |config|
  # Configure salt nodes
  config.vm.box = "centos_7.5.1804"
  config.vm.box_check_update = false
  config.vm.boot_timeout = 600
  config.vm.hostname = vm_name

  config.vm.provider :virtualbox do |vb, override|
    ## Network configuration
    #override.vm.network :private_network, ip: node['mgmt1'], virtualbox__intnet: "mgmt"

    # Headless
    vb.gui = false

    # name
    vb.name = vm_name

    # Virtual h/w specs
    vb.memory = vm_memory
    vb.cpus = vm_cpus

    # Use differencing disk instead of cloning entire VDI
    vb.linked_clone = true

    # Check if machine already provisioned
    if not File.exist?(File.join(Dir.pwd, "/.vagrant/machines/default/virtualbox/id"))
      # VDisk configuration start
      if not Dir.exist?(disks_dir)
        Dir.mkdir(disks_dir)
      end

      # SAS Controller
      vb.customize [ 'storagectl',
        :id,
        '--name', 'vdisk_vol',
        '--add', 'sas',
        '--controller', 'LSILogicSAS',
        '--portcount', disk_count,
        '--hostiocache', 'off',
        '--bootable', 'off'
      ]

      (1..disk_count).each do |disk_number|
        disk_file = File.expand_path(disks_dir).to_s + "/disk_#{disk_number}.vdi"

        # Note: Create a hard disk image: vboxmanage createmedium --filename $PWD/disk_<vm_name>_<disk_count>.vdi --size <disk_size> --format VDI
        if not File.exist?(disk_file)
          vb.customize ['createmedium',
            'disk',
            '--filename', disk_file,
            '--size', disk_size,
            '--format', 'VDI',
            '--variant', 'Standard'
          ]
        end

        # Attach hard disk
        # see https://www.virtualbox.org/manual/ch08.html#vboxmanage-storageattach
        vb.customize [
          'storageattach',
          :id,
          '--storagectl', 'vdisk_vol',
          '--port', disk_number - 1,
          '--device', 0,
          '--type', 'hdd',
          '--medium', disk_file,
          '--mtype', 'normal'
        ]
      end         # Disk creation loop
      # VDisk configuration end
    end           # Provisioned machine check
  end             # Virtualbox provisioner

  # Folder synchonization
  config.vm.synced_folder ".", "/opt/seagate/eos-prvsnr",
  create: true,
  disabled: false,
  type: "rsync",
  rsync__auto: true,
  rsync__exclude: [".git", ".gitignore", ".vagrant", "Vagrantfile"]

  # config.vm.synced_folder ".", "/opt/seagate/prvsnr-ees",
  # create: true,
  # disabled: false,
  # automount: true,
  # owner: "root",
  # group: "root"

  config.vm.provision :salt do |salt|
    # Master/Minion specific configs.
    salt.masterless = true
    salt.minion_config = './files/etc/salt/minion'

    # Generic configs
    salt.install_type = 'stable'
    salt.run_highstate = false
    salt.colorize = true
    salt.log_level = 'warning'
  end
end
