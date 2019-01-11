set -x
Output="./greatfire-domains.txt"

[ -f $Output ] && {
  cat $Output | xargs ./updater.py -a
  python3 ./find_redundant.py | xargs ./updater.py -d
}

