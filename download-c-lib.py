import urllib.request
import tarfile
from zipfile import ZipFile
import os
import re

# Script used to download objectbox-c shared libraries for all supported platforms. Execute by running `make get-lib`
# on first checkout of this repo and any time after changing the objectbox-c lib version.

version = "0.14.0"  # see objectbox/c.py required_version

release_url = f"https://github.com/objectbox/objectbox-c/releases/download/v{version}/objectbox-%s.%s"

# map between ./objectbox/lib paths and hashes in the conan_repo
# see https://github.com/objectbox/objectbox-c/blob/main/download.sh for the hashes
out_dir = "objectbox/lib"
release_configs = {
    # header file is the same for all platforms, get it from the linux x86_64 distributable
    "objectbox.h": {"conf": "linux-x64", "archiveExt": "tar.gz"},
    # linux
    "x86_64/libobjectbox.so": {"conf": "linux-x64", "archiveExt": "tar.gz"},
    "armv7l/libobjectbox.so": {"conf": "linux-x64", "archiveExt": "tar.gz"},
    "armv6l/libobjectbox.so": {"conf": "linux-x64", "archiveExt": "tar.gz"},
    # mac
    "x86_64/libobjectbox.dylib": {"conf": "macos-universal", "archiveExt": "zip"},
    # windows
    "AMD64/objectbox.dll": {"conf": "windows-x64", "archiveExt": "zip"},
}

base_dir = os.getcwd()

def fullmkdir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def download(rel_path: str):
    basename = os.path.basename(rel_path)
    archive_dir = "include" if basename.endswith(".h") else "lib"
    out_path = f"{out_dir}/{rel_path}"

    print("Downloading", out_path)
    fullmkdir(os.path.dirname(out_path))

    # Download the file from `url`, save it in a temporary directory and get the path to it (e.g. '/tmp/tmpb48zma')
    config = release_configs[rel_path]
    tmp_file, _ = urllib.request.urlretrieve(
        release_url % (config["conf"], config["archiveExt"])
    )

    # extract the file
    if config["archiveExt"] == "zip":
        with ZipFile(tmp_file, "r") as archive:
            with open(out_path, "wb") as out_file:
                out_file.write(archive.read(f"{archive_dir}/{basename}"))
    else:
        with tarfile.open(tmp_file, mode="r:gz") as archive:
            extract = archive.extractfile(f"{archive_dir}/{basename}")
            with open(out_path, "wb") as out_file:
                out_file.write(extract.read())


# execute the download for each item in the release configs
for key in release_configs:
    download(key)
