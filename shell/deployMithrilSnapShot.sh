#!/run/current-system/sw/bin/bash

export whi=`printf "\033[1;37m"`
export gre=`printf "\033[1;36m"`

tput clear

echo
echo $gre"Deploy Latest Mithril Mainnet Snapshot"
echo

### snapshots json url
snapshots="https://aggregator.release-mainnet.api.mithril.network/aggregator/artifact/snapshots"

# Get Json Snapshot Url
last_snapshot=$(curl -s $snapshots | jq -r .[0])

# Get Snapshot data
digest=$(echo $last_snapshot | jq -r '.digest')
echo $whi"Snapshot Digest: $gre$digest"

network=$(echo $last_snapshot | jq -r '.beacon.network')
echo $whi"Network: $gre$network"

epoch=$(echo $last_snapshot | jq -r '.beacon.epoch')
echo $whi"Epoch: $gre$epoch"

immutable_file_number=$(echo $last_snapshot | jq -r '.beacon.immutable_file_number')
echo $whi"Immutable File Number: $gre$immutable_file_number"

certificate_hash=$(echo $last_snapshot | jq -r '.certificate_hash')
echo $whi"Certificate Hash: $gre$certificate_hash"

size=$(echo $last_snapshot | jq -r '.size')
size_gb=$((size / 1024 / 1024))
size_gb_format=$(echo $size_gb | awk '{print substr($0, 1, length($0)-3) "." substr($0, length($0)-1)}')
echo $whi"Size: $gre$size_gb_format""Gb"

created_at=$(echo $last_snapshot | jq -r '.created_at' | awk '{print substr($0, 1, length($0)-11)}')
echo $whi"Created At: $gre$created_at"

compression_algorithm=$(echo $last_snapshot | jq -r '.compression_algorithm')
echo $whi"Compression Algorithm: $gre$compression_algorithm"

cardano_node_version=$(echo $last_snapshot | jq -r '.cardano_node_version')
echo $whi"Cardano Node Version: $gre$cardano_node_version"

downloadUrl=$(echo $last_snapshot | jq -r '.locations[]')
echo $whi"Download Url: $gre$downloadUrl"

echo
echo $whi"A highly compressed file will expand to roughly four times its size upon extraction."
echo
echo $whi"Please ensure you've enough space to perform this operation."
echo
echo $whi"Paste your Cardano Blockchain DB Path: "
echo
read -r inputPath

dbdir=$inputPath
echo

echo $whi"Latest Mithril Snapshot $gre$digest"
echo $whi"will be downloaded and deployed under directory: $gre$dbdir"
echo $gre

cd $dbdir

start_time=$(date "+%s")

wget -q --show-progress $downloadUrl
echo
echo $whi"Renaming $(ls $dbdir) to snapshot.tar.zst"
mv mainnet-*.tar.zst snapshot.tar.zst
echo
echo $whi"Deploying Lastest Mainnet Snapshot: $gre$snapDigest"
echo
echo "Extracting snapshot.tar.zst"
tar -xvf snapshot.tar.zst
echo
echo $whi"Deleting snapshot.tar.zst"
rm snapshot.tar.zst
echo
echo $whi"Cardano Blockchain DB has been restored under: $gre$dbDir"
echo $whi

ls -l $dbDir
echo

end_time=$(date "+%s")
elapsed=$(date -u -d @$((end_time - start_time)) +"%T")

echo "Elapsed hh:mm:ss $elapsed"
