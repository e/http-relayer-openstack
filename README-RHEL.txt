Rushstack
---------

To integrate Rushstack services with RHEL & CENTOS startup sequence, follow this steps:

1- Create rushstack OS user (the processes will run under this security account)
2- Copy init.d scripts to /etc/init.d
3- Set init scripts owner to root (chown root:root /etc/init/rushstack*.conf)
4- Configure automatic startup
	chkconfig --add rushstack-engine
	chkconfig --add rushstack-api
	