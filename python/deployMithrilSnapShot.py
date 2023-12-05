#!/bin/env python3

import os
import sys
import json
import requests
import tarfile
import threading
import time
import zstandard
from pathlib import Path
from datetime import datetime
from humanize import naturalsize
from progress.bar import ShadyBar
from progress.spinner import Spinner

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Download Mithril Snapshot
def download_with_progress(url, save_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))  / (1024 ** 3)
    block_size = 1024
    processed_size = 0

    # Progress bar for downloading
    with open(save_path, 'wb') as file, ShadyBar(' - Fetching Snapshot ', index=processed_size, max=total_size,
    suffix='    %(percent).1f%% - Downloaded: %(index)d/%(max)dGiB - Eta: %(eta)ds') as bar:

        for data in response.iter_content(block_size):
            file.write(data)
            processed_size += len(data) / (1024 ** 3)
            bar.goto(processed_size)

    bar.finish()

# Track File Size
class SizeTrackingFile:
    def __init__(self, file):
        self.file = file
        self.expanding_size = 0
        self.lock = threading.Lock()

    def write(self, data):
        self.file.write(data)
        with self.lock:
            self.expanding_size += len(data)

    def get_expanding_size_gb(self):
        with self.lock:
            return naturalsize(self.expanding_size, binary=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

# Add a global variable to signal the progress thread to stop
stop_progress_thread = False

def print_progress(file):
    # Hide the cursor
    print("\033[?25l", end="", flush=True)

    try:
        while not stop_progress_thread:
            time.sleep(0.1)
            print(f"\r - Decompressing {file.get_expanding_size_gb():<15}", end="", flush=True)
    finally:
        # Show the cursor
        print("\033[?25h", end="", flush=True)

# Decompress Snapshot
def decompress_snapshot(archive: Path, out_path: Path):
    global stop_progress_thread  # Declare the global variable

    archive = Path(archive).expanduser()
    out_path = Path(out_path).expanduser().resolve()

    dctx = zstandard.ZstdDecompressor()

    with archive.open("rb") as ifh:
        with SizeTrackingFile(open("snapshot.tar", "wb")) as ofh:
            progress_thread = threading.Thread(target=print_progress, args=(ofh,), daemon=True)
            progress_thread.start()

            dctx.copy_stream(ifh, ofh, read_size=8192, write_size=16384)

    stop_progress_thread = True  # Signal the progress thread to stop
    progress_thread.join()  # Wait for the progress thread to finish
    print(f"\r - Decompression completed. Snapshot Size: {ofh.get_expanding_size_gb():<15}")

# Unarchive Snapshot
def untar_snapshot(snapshot_tar: Path, out_path: Path):

    snapshot_tar = Path(snapshot_tar).expanduser()
    out_path = Path(out_path).expanduser().resolve()

    with tarfile.open(snapshot_tar) as z:
        total_size = sum(member.size for member in z.getmembers()) / 1024 / 1024 / 1024


        unarchive_spinner = Spinner(' - Deploying ')
        processed_size = 0

        for member in z.getmembers():
            z.extract(member, path=out_path)
            processed_size += member.size / 1024 / 1024 / 1024
            unarchive_spinner.next()
            unarchive_spinner.message = f' - Deploying ({processed_size:.1f} GiB of {total_size:.1f} GiB): '

        unarchive_spinner.finish()

# Run
def main():
      try:
       clear_screen()

       # white + green colors
       whi = "\033[1;37m"
       gre = '\033[92m'

       print()
       print(gre + "Mithril Snapshot Deployer")
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
           decompress_snapshot(db_dir / "snapshot.tar.zst", db_dir)
           os.remove(db_dir / "snapshot.tar.zst")
           print()
           untar_snapshot(db_dir / "snapshot.tar", db_dir)
           os.remove(db_dir / "snapshot.tar")
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
