#!/bin/bash

export white=`printf "\033[1;37m"`
export indi=`printf "\033[1;35m"`

tput clear

echo
echo $indi"Deploy Latest Mithril Mainnet Snapshot"
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
echo $white"A very large compressed file will be downloaded, take into account that once unarchived"
echo
echo $white"size will be about three times larger than compressed snapshot file."
echo
echo $white"Please ensure that you've enough space to perform this operation."
echo
echo $white"Paste your Cardano Blockchain DB Path: "
echo
read -r inputPath

dbdir=$inputPath
echo

echo $white"Latest Mithril Snapshot $indi$digest"
echo $white"will be downloaded and deployed under directory: $indi$dbdir"
echo $indi

cd $dbdir

start_time=$(date "+%s")

wget -q --show-progress $downloadUrl
echo
echo $white"Renaming $(ls $dbdir) to snapshot.tar.zst"
mv mainnet-*.tar.zst snapshot.tar.zst
echo
echo $white"Deploying Lastest Mainnet Snapshot: $indi$snapDigest"
echo
zstd -d snapshot.tar.zst
tar -xvf snapshot.tar
echo
echo $white"Deleting snapshot.tar.zst and snapshot.tar files"
rm snapshot.tar.zst snapshot.tar
echo
echo $white"Cardano Blockchain DB has been restored under: $indi$dbDir"
echo $white

ls -l $dbDir
echo

end_time=$(date "+%s")
elapsed=$(date -u -d @$((end_time - start_time)) +"%T")

echo "Elapsed hh:mm:ss $elapsed"
