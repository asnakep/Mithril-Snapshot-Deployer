#!/bin/env python3

import os
import sys
import json
import platform
import requests
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from progress.bar import Bar

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

def decompress_zst(archive: Path, out_path: Path):
    archive = Path(archive).expanduser()
    out_path = Path(out_path).expanduser().resolve()

    # If you are on Windows, ensure you've zstd.exe and tar.exe
    # under C:\Windows\System32
    if platform.system() == "Windows":
        # Get zstd for windows: https://sourceforge.net/projects/zstd-for-windows
        zstd_executable = os.path.join('C:\\', 'Windows', 'System32', 'zstd.exe')
        # Get tar for windows: https://gnuwin32.sourceforge.net/packages/gtar.htm
        tar_executable = os.path.join('C:\\', 'Program Files (x86)', 'GnuWin32', 'bin', 'tar.exe')
    else:
        zstd_executable = 'zstd'
        tar_executable = 'tar'

    # Use subprocess to call zstd for decompression
    zstd_process = subprocess.Popen(
        [zstd_executable, '--rm', '-d', '--stdout', str(archive)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Get total size for progress calculation
    total_size = os.path.getsize(archive) / 1024 / 1024
    chunk_size = 8192
    processed_size = 0

    try:
        with open(out_path / 'snapshot.tar', 'wb') as out_file, Bar('Decompressing snapshot.tar.zst:', fill='|', max=total_size, suffix='%(index)d/%(max)d Megabytes - %(percent).1f%% - %(eta)ds') as bar:
            while True:
                chunk = zstd_process.stdout.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)

                processed_size += len(chunk)  / 1024 / 1024
                bar.goto(processed_size)

    finally:
        # Wait for the process to finish
        zstd_process.wait()

        # Check for errors
        if zstd_process.returncode != 0:
            error_message = zstd_process.stderr.read().decode()
            print(f"\nError during decompression: {error_message}")

        # Close subprocess pipes
        zstd_process.stdout.close()
        zstd_process.stderr.close()

    print()

    # Now use tar for extraction
    tar_process = subprocess.Popen(
        [tar_executable, '-xf', 'snapshot.tar'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=out_path
    )

    # Get total size for progress calculation
    total_size_untar = os.path.getsize('snapshot.tar')
    chunk_size_untar = 8192
    processed_size_untar = 0

    # Create progress bar for untarring
    progress_untar = Bar('Unarchiving snapshot.tar', fill='|',max=total_size_untar, suffix='%(percent).1f%% - %(eta)ds')

    try:
        while True:
            chunk = tar_process.stdout.read(chunk_size_untar)
            if not chunk:
                break

            processed_size_untar += len(chunk)
            progress_untar.goto(processed_size_untar)

    finally:
        # Added this line to refresh the progress bar
        progress_untar.finish()

        # Wait for the process to finish
        tar_process.wait()

        # Check for errors
        if tar_process.returncode != 0:
            error_message = tar_process.stderr.read().decode()
            print(f"Error during unarchive: {error_message}")

    # Close subprocess pipes
    tar_process.stdout.close()
    tar_process.stderr.close()

# Run program:
def main():
      try:
       clear_screen()

       # white + green colors
       whi = "\033[1;37m"
       gre = '\033[92m'


       print()
       print(gre + "Latest Mithril Mainnet Snapshot - Download Only or Full Deploy ")
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
           print(whi + f"Downloading snapshot to: {gre}{db_dir / 'snapshot.tar.zst'}" + whi)
           print()
           download_with_progress(download_url, db_dir / "snapshot.tar.zst")
           print()
           print(whi + "Download complete.")
       elif choice == 'f':
           # Run the full script
           print()
           print(whi + f"Latest Mithril Snapshot {gre}{digest}")
           print(whi + f"will be downloaded and deployed under directory: {gre}{db_dir}")

           os.chdir(db_dir)
           start_time = datetime.now()
           print(whi)

           # Download with dynamic progress bar
           download_with_progress(download_url, db_dir / "snapshot.tar.zst")

           print()
           print(whi + f"Deploying Latest Mainnet Snapshot: {gre}{digest}")
           print(whi)

           # Extract contents of the Zstandard-compressed tar archive
           decompress_zst(db_dir / "snapshot.tar.zst", db_dir)
           print()

           print(whi + "Deleting snapshot.tar file")
           os.remove(db_dir / "snapshot.tar")

           print()
           print(whi + f"Latest Mithril Mainnet Snapshot has been restored under: {gre}{db_dir}")
           print(whi)
           print(os.listdir(db_dir))
           print()

           end_time = datetime.now()
           elapsed = end_time - start_time
           elapsed_str = str(elapsed).split('.')[0]
           print(f"Elapsed hh:mm:ss {elapsed_str}")
       else:
           print(whi + "Invalid choice. Please choose 'd' to download only or 'f' to run the full script.")

      except KeyboardInterrupt:
       print(whi + "\n\nScript interrupted.")
       print()
       sys.exit(0)

if __name__ == "__main__":
    main()
