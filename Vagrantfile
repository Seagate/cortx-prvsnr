# vi: set ft=ruby :

# Vagrantfile configuration fefernece:
#   https://www.vagrantup.com/docs/hyperv/configuration.html

# read vm configuration(s) from JSON file
require 'getoptlong'

def show_usage
  puts <<-EOF

USAGE:
  vagrant [OPTION] <vagrant options>

  --help:                       show help

  --singlenode | --ees:         default: singlenode.
  Where
        --singlenode: Single eos node VM.
        --ees: EES setup with 2 eos nodes.

  --with-s3client:              Create a S3 client VM.

  EOF
end

single_node_mode=false
ees_mode=false
create_s3client=false

opts = GetoptLong.new(
  [ '--singlenode', GetoptLong::OPTIONAL_ARGUMENT ],
  [ '--ees', GetoptLong::OPTIONAL_ARGUMENT ],
  [ '--help', GetoptLong::OPTIONAL_ARGUMENT ]
)

begin
  opts.each do |opt, arg|
    case opt
      when '--help'
        show_usage
        exit
      when '--singlenode'
        single_node_mode=true
        if ees_mode
          puts "ERROR: Only one option should be specified (--singlenode | --ees)"
          show_usage
          exit
        end
      when '--ees'
        ees_mode=true
        if single_node_mode
          puts "ERROR: Only one option should be specified (--singlenode | --ees)"
          show_usage
          exit
        end
      when '--with-s3client'
        create_s3client=true
    end
  end
rescue Exception => err
  puts "ERROR: %s." % err.message
  show_usage
  exit
end

salt_nodes = []
number_of_eos_nodes = 1 # default 1
if ees_mode
  number_of_eos_nodes = 2
end

last_octet_for_ip=100

for i in 1..number_of_eos_nodes
  last_octet_for_ip = last_octet_for_ip + i
  salt_nodes.push(
    {
      "name" => "eosnode-%d" % i,
      "cpus" => 2,
      "memory" => 4096,
      "mgmt0" => "172.16.10.%d" % last_octet_for_ip,
      "data0" => "172.19.10.%d" % last_octet_for_ip,
      "minion_id" => "eosnode-%d" % i
    }
  )
end

if create_s3client
  last_octet_for_ip = last_octet_for_ip + i
  salt_nodes.push(
    {
      "name"=> "s3client",
      "cpus"=> 2,
      "memory"=> 2048,
      "mgmt0" => "172.16.10.%d" % last_octet_for_ip,
      "data0" => "172.19.10.%d" % last_octet_for_ip,
      "minion_id" => "s3client"
    }
  )
end

# Disk configuration details
disks_dir = File.join(Dir.pwd, ".vdisks")
disk_count = 2
disk_size = 1024         # in MB

Vagrant.configure("2") do |config|

  salt_nodes.each do |node|
    config.vm.define node['name'] do |node_config|
      # Configure salt nodes
      node_config.vm.box_url = "http://ci-storage.mero.colo.seagate.com/prvsnr/vendor/centos/vagrant.boxes/centos_7.5.1804.box"
      node_config.vm.box_download_insecure = true
      node_config.vm.box = "centos_7.5.1804"
      node_config.vm.box_check_update = false
      node_config.vm.boot_timeout = 600
      node_config.vm.hostname = node['name']

      node_config.vm.provider :virtualbox do |vb, override|
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
      rsync__exclude: [".git", ".gitignore", ".vagrant", ".vdisks", "Vagrantfile"],
      rsync__verbose: true

      # Setup the ips in ifcfg sample files.

      node_config.vm.provision "shell",
        name: "Vagrant_override",
        #run: "once",
        inline: <<-SHELL
          echo IPADDR=#{node["mgmt0"]}
          echo IPADDR=#{node["data0"]}
          sudo sed -i 's/IPADDR=/IPADDR=#{node["mgmt0"]}/g' /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-mgmt0
          sudo sed -i 's/IPADDR=/IPADDR=#{node["data0"]}/g' /opt/seagate/ees-prvsnr/files/etc/sysconfig/network-scripts/ifcfg-data0
        SHELL

      node_config.vm.provision "shell",
        name: "Boootstrap EOS VM",
        run: "once",
        path: './files/scripts/setup/bootstrap-eos-vm.sh',
        privileged: true
      #
      # node_config.vm.provision "shell",
      #   name: "Vagrant_override",
      #   #run: "once",
      #   inline: <<-SHELL
      #     echo IPADDR=#{node["mgmt0"]}
      #     echo IPADDR=#{node["data0"]}
      #     sudo sed -i 's/IPADDR=/IPADDR=#{node["mgmt0"]}/g' /etc/sysconfig/network-scripts/ifcfg-mgmt0
      #     sudo sed -i 's/IPADDR=/IPADDR=#{node["data0"]}/g' /etc/sysconfig/network-scripts/ifcfg-data0
      #
      #     sudo ifdown enp0s8
      #     sudo ifdown enp0s9
      #     sudo ifdown data0
      #     sudo ifdown mgmt0
      #     sudo ifup data0
      #     sudo ifup mgmt0
      #
      #     sudo cp -R /opt/seagate/ees-prvsnr/files/etc/hosts /etc/hosts
      #
      #     touch /etc/salt/minion_id
      #     echo #{node["minion_id"]} |tee /etc/salt/minion_id
      #   SHELL

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
