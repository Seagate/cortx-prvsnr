# vi: set ft=ruby :

# Vagrantfile configuration fefernece:
#   https://www.vagrantup.com/docs/hyperv/configuration.html

# read vm configuration(s) from JSON file
salt_nodes = [
    {
        "name" => "ees-node1",
        "cpus" => 1,
        "memory" => 512,
        "maxmemory" => 1024,
        "mgmt0" => "172.16.10.101"
    },
    {
        "name"=> "ees-node2",
        "cpus"=> 1,
        "memory"=> 512,
        "maxmemory"=> 1024,
        "mgmt0" => "172.16.10.111"
    }
]

# Disk configuration details
disks_dir = File.join(Dir.pwd, ".vdisks")
disk_count = 2
disk_size = 256         # in MB

Vagrant.configure("2") do |config|
  # Configure salt nodes
  config.vm.box = "centos_7.5.1804"
  config.vm.box_check_update = false
  config.vm.boot_timeout = 600

  salt_nodes.each do |node|
    config.vm.define node['name'] do |node_config|
      node_config.vm.hostname = node['name']

      config.vm.provider :virtualbox do |vb, override|
        # Headless
        vb.gui = false

        # name
        vb.name = node['name']

        # Virtual h/w specs
        vb.memory = node['maxmemory']
        vb.cpus = node['cpus']

        # Use differencing disk instead of cloning entire VDI
        vb.linked_clone = true

        ## Network configuration
        override.vm.network :private_network, ip: node['mgmt0'], virtualbox__intnet: "mgmt"

        # Disable USB
        vb.customize ["modifyvm", :id, "--usb", "off"]
        vb.customize ["modifyvm", :id, "--usbehci", "off"]

        # Check if machine already provisioned
        if not File.exist?(File.join(Dir.pwd, "/.vagrant/machines/default/virtualbox/id"))
          # VDisk configuration start
          if not Dir.exist?(disks_dir)
            Dir.mkdir(disks_dir)
          end

          # SAS Controller - 1
          vb.customize [ 'storagectl',
            :id,
            '--name', "#{node['name']}_vdisk_vol_1",
            '--add', 'sas',
            '--controller', 'LSILogicSAS',
            '--portcount', 2,
            '--hostiocache', 'off',
            '--bootable', 'off'
          ]

          (1..disk_count).each do |disk_number|
            disk_file = File.expand_path(disks_dir).to_s + "/#{node['name']}_disk_#{disk_number}.vdi"

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
              '--storagectl', "#{node['name']}_vdisk_vol_1",
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
      node_config.vm.synced_folder ".", "/opt/seagate/ees-prvsnr",
      create: true,
      disabled: false,
      type: "rsync",
      rsync__auto: true,
      rsync__exclude: [".git", ".gitignore", ".vagrant", "Vagrantfile"]

      # node_config.vm.synced_folder ".", "/opt/seagate/prvsnr-ees",
      # create: true,
      # disabled: false,
      # automount: true,
      # owner: "root",
      # group: "root"

      node_config.vm.provision :salt do |salt|
        # Master/Minion specific configs.
        salt.masterless = true
        salt.minion_config = './files/etc/salt/minion'

        # Generic configs
        salt.install_type = 'stable'
        salt.run_highstate = false
        salt.colorize = true
        salt.log_level = 'warning'
      end

      node_config.vm.provision "file", source: "./files/.ssh", destination: "/home/vagrant/.ssh"

      node_config.vm.provision "shell", inline: <<-SHELL

        # ToDo
        # sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-eth* /etc/sysconfig/network-scripts/

        # sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-mgmt0 /etc/sysconfig/network-scripts/
        # sudo sed -i 's/IPADDR=/IPADDR=#{node['mgmt0']}/g' /etc/sysconfig/network-scripts/ifcfg-mgmt0

        # sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-data0 /etc/sysconfig/network-scripts/
        # sudo sed -i 's/IPADDR=/IPADDR=#{node['data0']}/g' /etc/sysconfig/network-scripts/ifcfg-data0

        # sudo cp -R /opt/seagate/ees-prvsnr/files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf

        # systemctl restart network.service

        sudo cp -R /opt/seagate/ees-prvsnr/files/etc/hosts /etc/hosts

        cat /home/vagrant/.ssh/id_rsa.pub>>/home/vagrant/.ssh/authorized_keys
        chmod 755 /home/vagrant/.ssh
        chmod 644 /home/vagrant/.ssh/*
        chmod 600 /home/vagrant/.ssh/id_rsa

        # sudo systemctl stop salt-minion
        # sudo systemctl disable salt-minion
      SHELL
    end
  end
end
