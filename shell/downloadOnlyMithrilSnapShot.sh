#!/run/current-system/sw/bin/bash

export white=`printf "\033[1;37m"`
export indi=`printf "\033[1;35m"`

tput clear

echo
echo $indi"Download Latest Mithril Mainnet Snapshot"
echo

### snapshots json url
snapshots="https://aggregator.release-mainnet.api.mithril.network/aggregator/artifact/snapshots"

# Get Json Snapshot Url
last_snapshot=$(curl -s $snapshots | jq -r .[0])

# Get Snapshot data
digest=$(echo $last_snapshot | jq -r '.digest')
echo $white"Snapshot Digest: $indi$digest"

network=$(echo $last_snapshot | jq -r '.beacon.network')
echo $white"Network: $indi$network"

epoch=$(echo $last_snapshot | jq -r '.beacon.epoch')
echo $white"Epoch: $indi$epoch"

immutable_file_number=$(echo $last_snapshot | jq -r '.beacon.immutable_file_number')
echo $white"Immutable File Number: $indi$immutable_file_number"

certificate_hash=$(echo $last_snapshot | jq -r '.certificate_hash')
echo $white"Certificate Hash: $indi$certificate_hash"

size=$(echo $last_snapshot | jq -r '.size')
size_gb=$((size / 1024 / 1024))
size_gb_format=$(echo $size_gb | awk '{print substr($0, 1, length($0)-3) "." substr($0, length($0)-1)}')
echo $white"Size: $indi$size_gb_format""Gb"

created_at=$(echo $last_snapshot | jq -r '.created_at' | awk '{print substr($0, 1, length($0)-11)}')
echo $white"Created At: $indi$created_at"

compression_algorithm=$(echo $last_snapshot | jq -r '.compression_algorithm')
echo $white"Compression Algorithm: $indi$compression_algorithm"

cardano_node_version=$(echo $last_snapshot | jq -r '.cardano_node_version')
echo $white"Cardano Node Version: $indi$cardano_node_version"

downloadUrl=$(echo $last_snapshot | jq -r '.locations[]')
echo $white"Download Url: $indi$downloadUrl"

echo
echo $white"A very large compressed file will be downloaded, size: $size_gb_format""Gb "
echo
echo $white"Please ensure that you've enough space to perform this operation."
echo
echo $white"Paste your Cardano Blockchain DB Path: "
echo
read -r inputPath

dbdir=$inputPath
echo

echo $white"Latest Mithril Snapshot $indi$digest"
echo $white"will be downloaded under directory: $indi$dbdir"
echo $indi

cd $dbdir

wget -q --show-progress $downloadUrl
