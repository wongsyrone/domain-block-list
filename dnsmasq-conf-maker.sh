ConfFile="./dnsmasq-blocklist.conf"
DefaultDomainList="./domains.txt"
DomainList="$1"

[ -f "$DefaultDomainList" ] && DomainListExists=1 || DomainListExists=0

[ "$1" == "" -a "$DomainListExists" == "0" ] && {
	echo "Notice: must cleanup old files before!"
	echo "the Default Domain List is $DefaultDomainList"
	echo "usage: $0 DOMAIN_LIST_FILE"
	exit 1
}

[ "$1" == "" -a "$DomainListExists" == "1" ] && {
	echo "using DefaultDomainList: $DefaultDomainList"
	DomainList=${DefaultDomainList}
}

rm -f $ConfFile 2>&1

echo -n "Only need ipset list? [y/n]:"
read NoServer
[ "$NoServer" == "y" -o "$NoServer" == "Y" ] || {
	echo -n "Enter your dns server (syntax IP[#port] ):"
	read dnsserver
	[ "$dnsserver" == "" ] && {
		dnsserver="8.8.8.8"
		echo "dns server empty, using 8.8.8.8 instead"
	}
	# in case using ':'
	dnsserver=${dnsserver//:/#}
}
echo -n "Enter your ipset name:"
read ipset
[ "$ipset" == "" ] && {
	ipset="UNKNOWN_IPSET_NAME"
	echo "ipset name empty!!"
}

cat $DomainList | while read SingleDomain
do
	echo "ipset=/$SingleDomain/${ipset}">>$ConfFile
	[ "$NoServer" == "y" -o "$NoServer" == "Y" ] || {
		echo "server=/$SingleDomain/${dnsserver}">>$ConfFile
	}
done
