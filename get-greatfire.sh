set -x
Output="./greatfire.txt"
[ -f $Output ] && {
  rm -f $Output
}
Threshold=70
for i in $( seq 0 10 )
do
#https://zh.greatfire.org/search/domains?
curl -s --insecure "https://zh.greatfire.org/search/alexa-top-1000-domains?page=$i"|  \
grep 'class="first"' | grep 'class="blocked"' | grep -vE "google"|\
sed -e "s#^[^\/]*\/\([^\"]*\)[^\%]*\%...\([^\%]*\)\%.*#\1 \2#g"|\
#awk '$2>='"$Threshold"' {printf $1 "\t" $2 "\n"}' 
awk '$2>='"$Threshold"' {print ""$1"" }'\
>>$Output
curl -s --insecure "https://zh.greatfire.org/search/domains?page=$i"|  \
grep 'class="first"' | grep 'class="blocked"' | grep -vE "google"|\
grep -vE "facebook"| grep -vE "twitter"|\
sed -e "s#^[^\/]*\/\([^\"]*\)[^\%]*\%...\([^\%]*\)\%.*#\1 \2#g"|\
sed -e "s#^https/##g" |\
#awk '$2>='"$Threshold"' {printf $1 "\t" $2 "\n"}' 
awk '$2>='"$Threshold"' {print ""$1"" }'\
>>$Output
done

cat $Output | xargs ./updater.py -a
