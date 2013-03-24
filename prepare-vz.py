from socket import getdefaulttimeout, setdefaulttimeout
from fabric.api import *
from fabric.colors import *
from fabric.utils import *
import string


env.password = "root"
env.user = "root"
env.port = "22"
env.warn_only = True
env.skip_bad_hosts = True

@task
def prepare_hn(reboot="no"):
	run('yum -y install sudo')
	run('yum -y install wget')

	templatevz = "centos-6-x86_64"
	with hide('warnings','running','stderr','stdout'):
		execute(epel_setup)
		execute(openvz_setup)
		print(cyan('['+env.host+'] descargando template: ' + templatevz))
		execute(openvz_templatesetup,templatevz)
	#if reboot=="yes":
	#	print('reiniciando ....')
	#	sudo('shutdown -r now')
	#	local('ping ' + env.host)

def epel_setup():
	epelurl = "http://dl.fedoraproject.org/pub/epel/6/"
	epelrelease = "6-8"
	epel = sudo('stat /etc/yum.repos.d/epel.repo')
	if epel.return_code != int(0):
		print(cyan('['+env.host+'] instalando epel (release: ' + epelrelease + ')...'))
		sudo('yum -y install ' + epelurl + '$(uname -p)' + '/epel-release-' + epelrelease + '.noarch.rpm')
		print(green('['+env.host+'] epel instalado ...'))
	else:
		print(yellow('['+env.host+'] epel ya instalado'))

def openvz_setup():
	ovzrepo = sudo('stat /etc/yum.repos.d/openvz.repo')
	if ovzrepo.return_code != 0:
		print(cyan('['+env.host+'] instalando repo y kernel'))
		sudo('wget -P /etc/yum.repos.d/ http://download.openvz.org/openvz.repo')
		sudo('rpm --import  http://download.openvz.org/RPM-GPG-Key-OpenVZ')
		print(green('['+env.host+'] repo ok'))
		sudo('yum -y install vzkernel')
		sudo('yum -y install vzctl')
		sudo('chkconfig vzeventd on')
		sudo('chkconfig vz on')
		print(green('['+env.host+'] kernel ok'))
	else:
		print(yellow('[' + env.host + '] kernel vz ya instalado'))

def openvz_templatesetup(template):
	#sudo('wget -P /vz/template/cache/ http://download.openvz.org/template/precreated/' + template + '.tar.gz')
	sudo('rsync -avz http://download.openvz.org/template/precreated/' + template + '.tar.gz /vz/template/cache/')
	print(green('['+env.host+'] template: ' + template + ' ok'))



@task
def create_machine(num=0,template="centos",basename="vz",config="light",network="192.168.1"):
	with hide('warnings','running','stderr','stdout'):
		if num==0:
			sudo('vzctl create 100 --ostemplate centos-6-x86_64 --hostname vz01 --config light')
		else:
			veids = []
			start_veid = 100
			end_veid = 200
			while (start_veid <= end_veid):
				if len(veids)<=int(num):
					nn = str(start_veid)
					veid = sudo('stat /etc/vz/conf/'+nn+'.conf')
					if veid.return_code !=0:
						veids.append(start_veid)	
				else:
					break
				start_veid = start_veid + 1	
			
			print(cyan("Determinando ips disponibles ..."))
			ipdet = sudo('nmap -sP '+network+'.1-254 -vv|grep down|awk \'{print $5}\'|head -n '+num+'|tr "\r\n" ","')
			gaga = string.split(ipdet,",")
			total = 0
			while(total < int(num)):
				createveid=str(veids[total])
				print(green('['+createveid+']: creando '+template+' ('+config+') con ip: '+gaga[total]))
				sudo('vzctl create '+createveid+' --ostemplate centos-6-x86_64 --hostname vz'+createveid+' --config light')
				sudo('vzctl set '+createveid+' --ipadd '+gaga[total]+' --save')
				print('ok')
				total = total + 1

