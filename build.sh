#!/bin/sh

version=$( cat evcc/version | tr -d " \t\n\r" )
url="https://github.com/evcc-io/evcc/releases/download/${version}/evcc_${version}_linux-armv6.tar.gz"

printf "loading and unpacking evcc version $version ... "
wget -qO- "$url" | tar xz -C evcc
echo "done"

rm evcc/evcc.dist.yaml

printf "packing venus-data.tar.gz ... "
[ -f venus-data.tar.gz ] && rm venus-data.tar.gz
if [ "$(uname)" = "Darwin" ]; then
    tar --disable-copyfile --exclude='.DS_Store' -czf venus-data.tar.gz evcc rc
else
    tar -czf venus-data.tar.gz evcc rc
fi
echo "done"

echo "ready for install"
