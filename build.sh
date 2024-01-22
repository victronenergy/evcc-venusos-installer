#!/bin/sh

version=$( cat evcc/version | tr -d " \t\n\r" )
url="https://github.com/evcc-io/evcc/releases/download/${version}/evcc_${version}_linux-armv6.tar.gz"

printf "loading and unpacking evcc version $version ... "
curl --silent --output - -L "$url" | tar xz -C evcc
rm evcc/evcc.dist.yaml
echo "done"

printf "loading and unpacking pyyaml package ... "
curl --silent --output - -L "https://github.com/yaml/pyyaml/archive/refs/tags/6.0.1.tar.gz" | tar xz -C evcc/
echo "done"

printf "copying evcc.yaml configuration ... "
if [ -f evcc.yaml ]; then
    cp evcc.yaml ./evcc/evcc.custom.yaml
else
    cp evcc.dist.yaml ./evcc/evcc.custom.yaml
fi
echo "done"

printf "packing venus-data.tar.gz ... "
[ -f venus-data.tar.gz ] && rm venus-data.tar.gz
if [ "$(uname)" = "Darwin" ]; then
    tar --disable-copyfile --exclude='.DS_Store' -czf venus-data.tar.gz evcc rc
else
    tar -czf venus-data.tar.gz evcc rc
fi
echo "done"

echo "ready for install"
