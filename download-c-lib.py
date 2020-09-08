import urllib.request
import tarfile
import os

version = "0.6.0"  # see objectbox/c.py required_version

conan_repo = "https://dl.bintray.com/objectbox/conan/objectbox/objectbox-c"
conan_channel = "testing"

# map between ./objectbox/lib paths and hashes in the conan_repo
# see https://github.com/objectbox/objectbox-c/blob/main/download.sh for the hashes
out_dir = "objectbox/lib"
file_hashes = {
    # objectbox.h is common for all types, get it from the linux x86_64 distributable
    "objectbox.h": "4db1be536558d833e52e862fd84d64d75c2b3656",

    # linux
    "x86_64/libobjectbox.so": "4db1be536558d833e52e862fd84d64d75c2b3656",
    "armv7l/libobjectbox.so": "4a625f0bd5f477eacd9bd35e9c44c834d057524b",
    "armv6l/libobjectbox.so": "d42930899c74345edc43f8b7519ec7645c13e4d8",

    # mac
    "x86_64/libobjectbox.dylib": "46f53f156846659bf39ad6675fa0ee8156e859fe",

    # windows
    "AMD64/objectbox.dll": "ca33edce272a279b24f87dc0d4cf5bbdcffbc187",
}


def url_for(rel_path: str) -> str:
    return conan_repo + "/" + version + "/" + conan_channel + "/0/package/" \
           + file_hashes[rel_path] + "/0/conan_package.tgz"


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
    tmp_file, headers = urllib.request.urlretrieve(url_for(rel_path))

    # extract the file
    archive = tarfile.open(tmp_file, mode='r:gz')
    archived_file = archive.extractfile(archive_dir + "/" + basename)
    with open(out_path, 'wb') as file:
        file.writelines(archived_file.readlines())


# execute the download for each item in the file hashes
for key in file_hashes:
    download(key)
