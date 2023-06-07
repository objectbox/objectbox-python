import urllib.request
import tarfile
import zipfile
import os

# Script used to download objectbox-c shared libraries for all supported platforms. Execute by running `make get-lib`
# on first checkout of this repo and any time after changing the objectbox-c lib version.

version = "v0.18.1"  # see objectbox/c.py required_version
variant = 'objectbox'  # or 'objectbox-sync'

base_url = "https://github.com/objectbox/objectbox-c/releases/download/"

# map between ./objectbox/lib paths and artifact suffixes at https://github.com/objectbox/objectbox-c/releases
out_dir = "objectbox/lib"
files = {
    # header file is the same for all platforms, get it from the linux x86_64 distributable
    "objectbox.h": "linux-x64.tar.gz",

    # linux
    "x86_64/libobjectbox.so": "linux-x64.tar.gz",
    "aarch64/libobjectbox.so": "linux-aarch64.tar.gz",
    "armv7l/libobjectbox.so": "linux-armv7hf.tar.gz",
    "armv6l/libobjectbox.so": "linux-armv6hf.tar.gz",

    # mac
    "macos-universal/libobjectbox.dylib": "macos-universal.zip",

    # windows
    "AMD64/objectbox.dll": "windows-x64.zip",
}

def url_for(rel_path: str) -> str:
    return base_url + "/" + version + "/" + variant + "-" + files[rel_path]


def fullmkdir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def download(rel_path: str):
    basename = os.path.basename(rel_path)
    archive_dir = "include" if basename.endswith(".h") else "lib"
    out_path = out_dir + "/" + rel_path

    print("Downloading", out_path)
    fullmkdir(os.path.dirname(out_path))

    # Download the file from `url`, save it in a temporary directory and get the path to it (e.g. '/tmp/tmpb48zma')
    source_url = url_for(rel_path);
    tmp_file, headers = urllib.request.urlretrieve(source_url)

    # extract the file
    with open(out_path, 'wb') as file:
        if source_url.endswith('.zip'):
            with zipfile.ZipFile(tmp_file) as archive:
                with archive.open(archive_dir + "/" + basename) as archived_file:
                    file.writelines(archived_file.readlines())
        else:
            with tarfile.open(tmp_file, mode='r:gz') as archive:
                with archive.extractfile(archive_dir + "/" + basename) as archived_file:
                    file.writelines(archived_file.readlines())


# execute the download for each item in the file hashes
for key in files:
    download(key)
