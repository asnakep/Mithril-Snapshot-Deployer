#!/bin/env python3

#!/bin/env python3

import os
import json
from datetime import datetime
import requests
from tqdm import tqdm
import shutil
from pathlib import Path
import tempfile
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def download_with_progress(url, save_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    tqdm_bar = tqdm(total=total_size, unit='iB', unit_scale=True, dynamic_ncols=True, bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:40}{r_bar}')

    with open(save_path, 'wb') as file:
        for data in response.iter_content(block_size):
            tqdm_bar.update(len(data))
            file.write(data)

    tqdm_bar.close()

def extract_zst(archive_path: Path, out_path: Path):
    archive_path = Path(archive_path).expanduser()
    out_path = Path(out_path).expanduser().resolve()

    # Uncompress using zstd
    uncompressed_file = out_path / "snapshot.tar"
    subprocess.run(["zstd", "-d", str(archive_path), "--output", str(uncompressed_file)])

    # Untar using tar
    subprocess.run(["tar", "-xvf", str(uncompressed_file), "-C", str(out_path)])



def main():
    try:
      clear_screen()
      
      # white + indigo colors
      whi = "\033[1;37m"
      ind = "\033[1;35m"
      
      print(ind + "Deploy Latest Mithril Mainnet Snapshot")
      print()
      
      snapshots_url = "https://aggregator.release-mainnet.api.mithril.network/aggregator/artifact/snapshots"
      response = requests.get(snapshots_url)
      last_snapshot = response.json()
      
      snapshot_info = last_snapshot[0]["beacon"]
      digest = last_snapshot[0]["digest"]
      size_gb = last_snapshot[0]["size"] / 1024 / 1024 / 1024
      size_gb_format = f"{size_gb:.2f}"
      created_at =   last_snapshot[0]["created_at"][:19]
      download_url = last_snapshot[0]["locations"][0]
      
      print(whi + f"Snapshot Digest: {ind}{digest}")
      print(whi + f"Network: {ind}{snapshot_info['network']}")
      print(whi + f"Epoch: {ind}{snapshot_info['epoch']}")
      print(whi + f"Immutable File Number: {ind}{snapshot_info['immutable_file_number']}")
      print(whi + f"Certificate Hash: {ind}{last_snapshot[0]['certificate_hash']}")
      print(whi + f"Size: {ind}{size_gb_format}Gb")
      print(whi + f"Created At: {ind}{created_at}")
      print(whi + f"Compression Algorithm: {ind}{last_snapshot[0]['compression_algorithm']}")
      print(whi + f"Cardano Node Version: {ind}{last_snapshot[0]['cardano_node_version']}")
      print(whi + f"Download Url: {ind}{download_url}")
      
      print()
      print(whi + "A very large compressed file will be downloaded, take into account that once unarchived")
      print(whi + "size will be about four times larger than compressed snapshot file.")
      print(whi + "Please ensure that you've enough space to perform this operation.")
      print()
      input_path = input(whi + "Paste your Cardano Blockchain DB Path: \n\n")
      db_dir = Path(input_path.strip()).resolve()
      
      print()
      print(whi + f"Latest Mithril Snapshot {ind}{digest}")
      print(whi + f"will be downloaded and deployed under directory: {ind}{db_dir}")
      
      os.chdir(db_dir)
      
      start_time = datetime.now()
      
      print(ind)
      
      # Download with dynamic progress bar
      download_with_progress(download_url, "snapshot.tar.zst")
      
      print()
      print(whi + f"Deploying Latest Mainnet Snapshot: {ind}{digest}")
      
      # Extract contents of the Zstandard-compressed tar archive
      extract_zst(db_dir / "snapshot.tar.zst", db_dir)
      
      print()
      print(whi + "Deleting snapshot.tar.zst file")
      os.remove("snapshot.tar.zst")
      print()
      print(whi + f"Latest Mithril Mainnet Snapshot has been restored under: {ind}{db_dir}")
      print(whi)
      print(os.listdir(db_dir))
      print()
      
      end_time = datetime.now()
      elapsed = end_time - start_time
      elapsed_str = str(elapsed).split('.')[0]
      print(f"Elapsed hh:mm:ss {elapsed_str}")

    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
