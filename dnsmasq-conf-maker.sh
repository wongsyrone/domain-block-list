ConfFile="./dnsmasq-blocklist.conf"
DefaultDomainList="./domains.txt"
DomainList="$1"

if [ -f "$DefaultDomainList" ]; then
	DomainListExists=1
else
	DomainListExists=0
fi

if [ "$1" == "" -a "$DomainListExists" == "0" ]; then
	echo "Notice: must cleanup old files before!"
	echo "the Default Domain List is $DefaultDomainList"
	echo "usage: $0 DOMAIN_LIST_FILE"
	exit 1
fi

if [ "$1" == "" -a "$DomainListExists" == "1" ]; then
	echo "using DefaultDomainList: $DefaultDomainList"
	DomainList=${DefaultDomainList}
fi

rm -f $ConfFile 2>&1

echo -n "Enter your dns server (syntax IP[#port] ):"
read dnsserver
if [ "$dnsserver" == "" ]; then
	dnsserver="8.8.8.8"
	echo "dns server empty, using 8.8.8.8 instead"
fi
# in case using ':'
dnsserver=${dnsserver//:/#}
echo -n "Enter your ipset name:"
read ipset
if [ "$ipset" == "" ]; then
	ipset="UNKNOWN_IPSET_NAME"
	echo "ipset name empty!!"
fi

cat $DomainList | while read SingleDomain
do
	echo "ipset=/$SingleDomain/${ipset}">>$ConfFile
	echo "server=/$SingleDomain/${dnsserver}">>$ConfFile
done
