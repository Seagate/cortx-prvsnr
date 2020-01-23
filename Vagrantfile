# vi: set ft=ruby :

# Vagrantfile configuration fefernece:
#   https://www.vagrantup.com/docs/hyperv/configuration.html

# read vm configuration(s) from JSON file
salt_nodes = [
  {
    "name" => "eosnode-1",
    "cpus" => 2,
    "memory" => 2048,
    "mgmt0" => "172.16.10.101",
    "data0" => "172.19.10.101",
    "minion_id" => "eosnode-1"
  },
  {
    "name"=> "eosnode-2",
    "cpus"=> 2,
    "memory"=> 2048,
    "mgmt0" => "172.16.10.102",
    "data0" => "172.19.10.102",
    "minion_id" => "eosnode-2"
  },
  {
    "name"=> "s3client",
    "cpus"=> 2,
    "memory"=> 2048,
    "mgmt0" => "172.16.10.103",
    "data0" => "172.19.10.103",
    "minion_id" => "s3client"
  }
]

Vagrant.configure("2") do |config|

  salt_nodes.each do |node|
    config.vm.define node['name'] do |node_config|
      
      node_config.vm.provider :hyperv do |hv, override|
        # Configure salt nodes
        override.vm.box_url = "http://ci-storage.mero.colo.seagate.com/prvsnr/vendor/centos/vagrant.boxes/centos_7.7.1908_hyperv.box"
        override.vm.box_download_insecure = true
        override.vm.box = "centos_7.7.1908_hyperv"
        override.vm.box_check_update = false
        override.vm.boot_timeout = 600
        override.vm.hostname = node['name']

        # name
        # Name of VM
        hv.vmname = node['name']

        # Virtual h/w specs
        hv.cpus = node['cpus']
        hv.memory = 512
        hv.maxmemory = node['memory']

        # Don't use differencing disk instead of cloning entire VDI
        hv.linked_clone = false

        # Enable virtualization extensions
        hv.enable_virtualization_extensions = true

        # Enable checkpoints
        hv.enable_checkpoints = false

        # Enable automatic checkpoints
        hv.enable_automatic_checkpoints = false

        # Number of seconds to wait for the VM to report an IP address.
        hv.ip_address_timeout = 300

        # Set the state of integration services for hyperv
        # Reference:
        #   https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/reference/integration-services
        hv.vm_integration_services = {
            # Allows the host to trigger virtual machines shutdown.
            shutdown: true,

            # Synchronizes the virtual machine's clock with the host computer's clock.
            time_synchronization: true,

            # Provides a way to exchange basic metadata between the virtual machine and the host.
            key_value_pair_exchange: true,

            #Reports that the virtual machine is running correctly.
            heartbeat: true,

            # Allows Volume Shadow Copy Service to back up the virtual machine with out shutting it down.
            vss: false,

            # Provides an interface for the Hyper-V host to copy files to or from the virtual machine.
            guest_service_interface: true,
        }
      end             # Hyper-V provisioner

      node_config.vm.provider :virtualbox do |vb, override|
        # Configure salt nodes
        override.vm.box_url = "http://ci-storage.mero.colo.seagate.com/prvsnr/vendor/centos/vagrant.boxes/centos_7.7.1908_vbox.box"
        override.vm.box_download_insecure = true
        override.vm.box = "centos_7.7.1908_vbox"
        override.vm.box_check_update = false
        override.vm.boot_timeout = 600
        override.vm.hostname = node['name']

        # Disk configuration details: For Virtualbox provider only
        disks_dir = File.join(Dir.pwd, ".vagrant", "vdisks")
        disk_count = 2
        disk_size = 2048         # in MB

        # Headless
        vb.gui = false

        # name
        vb.name = node['name']

        # Virtual h/w specs
        vb.memory = node['memory']
        vb.cpus = node['cpus']

        # Use differencing disk instead of cloning entire VDI
        vb.linked_clone = false

        ## Network configuration
        override.vm.network :private_network, ip: node['mgmt0'], virtualbox__intnet: "mgmt0"
        override.vm.network :private_network, ip: node['data0'], virtualbox__intnet: "data0"

        # Disable USB
        vb.customize ["modifyvm", :id, "--usb", "off"]
        vb.customize ["modifyvm", :id, "--usbehci", "off"]

        unless 's3client' == node['name']
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
                  '--size', disk_size * disk_number,
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
            end       # Disk creation loop
            # VDisk configuration end
          end         # Provisioned machine check
        end           # End of Unless
      end             # Virtualbox provisioner

      # Folder synchonization
      node_config.vm.synced_folder ".", "/opt/seagate/ees-prvsnr",
        type: "rsync",
        rsync__args: ["--archive", "--delete", "-z", "--copy-links"],
        rsync__auto: true,
        rsync__exclude: [".vagrant", "Vagrantfile"],
        rsync__verbose: true

      node_config.vm.provision "shell",
        name: "Boootstrap VM",
        run: "once",
        path: './files/scripts/setup/bootstrap.sh',
        privileged: true

      node_config.vm.provision "shell",
        name: "Vagrant_override",
        #run: "once",
        inline: <<-SHELL
          # Setup data0 network
          sudo cp /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-data0 /etc/sysconfig/network-scripts/
          echo IPADDR=#{node["data0"]}
          sudo sed -i 's/IPADDR=/IPADDR=#{node["data0"]}/g' /etc/sysconfig/network-scripts/ifcfg-data0

          touch /etc/salt/minion_id
          sudo echo #{node["minion_id"]} > /etc/salt/minion_id
          sudo sed -i 's/master: .*/master: 127.0.0.1/g' /etc/salt/minion

          sudo salt-key -D
          sudo systemctl restart salt-minion
          sleep 2
          sudo salt-key -A -y
          sleep 2

          #sudo salt eosnode-1 state.apply components.system
          #sudo salt eosnode-1 state.apply components.system.storage
          #sudo salt eosnode-1 state.apply components.ha.haproxy
          #sudo salt eosnode-1 state.apply components.misc.build_ssl_cert_rpms
          #sudo salt eosnode-1 state.apply components.misc.openldap
          #sudo salt eosnode-1 state.apply components.sspl
          #sudo salt eosnode-1 state.apply components.eoscore
          #sudo salt eosnode-1 state.apply components.halon
          #sudo salt eosnode-1 state.apply components.s3server
          #sudo salt eosnode-1 state.apply components.post_setup
        SHELL

      #unless 's3client' == node['name']
      #  node_config.vm.provision :salt do |salt|
      #    # Master/Minion specific configs.
      #    salt.masterless = true
      #    salt.minion_config = './files/etc/salt/minion'
      #
      #    # Generic configs
      #    salt.install_type = 'stable'
      #    salt.run_highstate = false
      #    salt.colorize = true
      #    salt.log_level = 'warning'
      #  end     # End of Salt Provisioning
      #end       # End of Unless
    end
  end
end
