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

## append special ipset to Conffile, we don't have to exclude dl.google.com anymore
# this will not add domains to ipset list, pls refer to dnsmasq manpage
echo "#### Bypass ipset domains">>$ConfFile
#echo "ipset=/dl.google.com/#">>$ConfFile
cat <<'EOF' | while read BypassIpsetDomain
265.com
2mdn.net
csi.gstatic.com
dl.google.com
doubleclick.net
fonts.googleapis.com
fonts.gstatic.com
google-analytics.com
googleadservices.com
googleanalytics.com
googlesyndication.com
googletagmanager.com
googletagservices.com
mediavisor.doubleclick.com
redirector.gvt1.com
EOF
do
    echo "ipset=/$BypassIpsetDomain/#" >>$ConfFile
done

