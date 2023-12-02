#!/bin/env python3

import os
import sys
import json
import requests
import tarfile
import tempfile
import zstandard
from pathlib import Path
from datetime import datetime
from progress.bar import ChargingBar
from progress.spinner import Spinner

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Download Mithril Snapshot
def download_with_progress(url, save_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))  / (1024 ** 3)
    block_size = 1024
    processed_size = 0

    # Create progress bar for downloading
    with open(save_path, 'wb') as file, ChargingBar(' - Fetching Snapshot ', index=processed_size, max=total_size,
    suffix='    %(percent).1f%% - Downloaded: %(index)d/%(max)dGb - Eta: %(eta)ds') as bar:

        for data in response.iter_content(block_size):
            file.write(data)
            processed_size += len(data) / (1024 ** 3)
            bar.goto(processed_size)

    bar.finish()

# Decompress/Unarchive Mithril Snapshot
def deploy_snaphot(archive: Path, out_path: Path):

    archive = Path(archive).expanduser()
    out_path = Path(out_path).expanduser().resolve()

    dctx = zstandard.ZstdDecompressor()

    with tempfile.TemporaryFile(suffix=".tar") as ofh:
        with archive.open("rb") as ifh:
            dctx.copy_stream(ifh, ofh)
        ofh.seek(0)
        with tarfile.open(fileobj=ofh) as z:
            # Get the number of members in the archive for the spinner
            total_members = len(z.getmembers())

            with Spinner(' - Deploying ') as spinner:
                for member in z.getmembers():
                    z.extract(member, path=out_path)
                    spinner.next()

# Run
def main():
      try:
       clear_screen()

       # white + green colors
       whi = "\033[1;37m"
       gre = '\033[92m'

       print()
       print(gre + "Latest Mithril Mainnet Snapshot")
       print()

       snapshots_url = "https://aggregator.release-mainnet.api.mithril.network/aggregator/artifact/snapshots"
       response = requests.get(snapshots_url)
       last_snapshot = response.json()

       snapshot_info = last_snapshot[0]["beacon"]
       digest = last_snapshot[0]["digest"]
       size_gb = last_snapshot[0]["size"] / 1024 / 1024 / 1024
       size_gb_format = f"{size_gb:.2f}"
       created_at = last_snapshot[0]["created_at"][:19]
       download_url = last_snapshot[0]["locations"][0]

       print(whi + f"Snapshot Digest: {gre}{digest}")
       print(whi + f"Network: {gre}{snapshot_info['network']}")
       print(whi + f"Epoch: {gre}{snapshot_info['epoch']}")
       print(whi + f"Immutable File Number: {gre}{snapshot_info['immutable_file_number']}")
       print(whi + f"Certificate Hash: {gre}{last_snapshot[0]['certificate_hash']}")
       print(whi + f"Size: {gre}{size_gb_format}Gb")
       print(whi + f"Created At: {gre}{created_at}")
       print(whi + f"Compression Algorithm: {gre}{last_snapshot[0]['compression_algorithm']}")
       print(whi + f"Cardano Node Version: {gre}{last_snapshot[0]['cardano_node_version']}")
       print(whi + f"Download Url: {gre}{download_url}")

       print()
       print(whi + "A highly compressed file will expand to roughly four times its size upon extraction.")
       print(whi + "Please ensure you've enough space to perform this operation.")
       print()

       # Get the directory path from the user
       input_path = input(whi + "Paste full path directory target: ")
       db_dir = Path(input_path.strip()).resolve()

       # Offer options to the user
       print()
       print(whi + "1. Download snapshot (press d)")
       print(whi + "2. Full snapshot deployment (press f)")
       print()
       choice = input(whi + "> ").strip().lower()

       if choice == 'd':
           # Download only
           print()
           print(whi + f"Downloading Snapshot to: {gre}{db_dir / 'snapshot.tar.zst'}" + whi)
           print()
           download_with_progress(download_url, db_dir / "snapshot.tar.zst")
           print()
           print(whi + "Download complete.")
       elif choice == 'f':
           # Run the full script
           print()
           print(whi + f"Latest Mithril Snapshot {gre}{digest}")
           print()
           print(whi + f"Will be downloaded and deployed under directory: {gre}{db_dir}")

           os.chdir(db_dir)
           start_time = datetime.now()
           print(whi)

           # Download with dynamic progress bar
           download_with_progress(download_url, db_dir / "snapshot.tar.zst")

           # Decompress and Extract contents of the Zstandard-compressed tar archive
           deploy_snaphot(db_dir / "snapshot.tar.zst", db_dir)
           os.remove(db_dir / "snapshot.tar.zst")
           print()
           print(whi + f"Snapshot has been restored under: {gre}{db_dir}")
           print(whi)
           print(os.listdir(db_dir))
           print()
           end_time = datetime.now()
           elapsed = end_time - start_time
           elapsed_str = str(elapsed).split('.')[0]
           print(f"Elapsed hh:mm:ss {elapsed_str}")
           print()
       else:
           print(whi + "Invalid choice. Please choose 'd' to download only or 'f' to run the full script.")

      except KeyboardInterrupt:
       print(whi + "\n\nScript interrupted.")
       print()
       sys.exit(0)

if __name__ == "__main__":
    main()
