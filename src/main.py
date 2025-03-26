import os

from config import FIREBASE_PERSONAL_ROOT_FOLDER, WORKING_FOLDER
from sync.firebase.utils import copy, delete, download, get_url, list_files, upload

if __name__ == "__main__":
    # Download from firebase:
    results = download()
    for result in results:
        print(f"Downloading {result[0]} to {result[1]}")

    results = upload(os.path.join(WORKING_FOLDER, "empty.txt"))
    print(f"Uploading {results[0]} to {results[1]}")

    results = upload(os.path.join(WORKING_FOLDER, "sub_dir/empty.txt"))
    print(f"Uploading {results[0]} to {results[1]}")

    results = upload(WORKING_FOLDER, recursive=True)
    for result in results:
        print(f"Uploading {result[0]} to {result[1]}")

    results = copy(FIREBASE_PERSONAL_ROOT_FOLDER, os.path.join(FIREBASE_PERSONAL_ROOT_FOLDER, "bak/"))
    for result in results:
        print(f"Copying {result[0]} to {result[1]}")

    results = delete(os.path.join(FIREBASE_PERSONAL_ROOT_FOLDER, "sub_dir/sub_sub_dir"))
    for result in results:
        print(f"Deleting {result}")

    files = list_files(recursive=True)
    print("Remote files:")
    for file in files:
        url = get_url(file)
        print(f"    {file} - {url}")
