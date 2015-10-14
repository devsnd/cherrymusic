Vagrant.configure("2") do |config|
	# Base Ubuntu Box 
	config.vm.box = "ubuntu/trusty64"
	config.vm.synced_folder ".", "/var/www"
	config.vm.provision :shell, path: "bootstrap.sh"
	config.vm.network :forwarded_port, guest: 8080, host: 8080 
end