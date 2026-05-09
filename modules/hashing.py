import hashlib


def hash_file(path):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
            sha1.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest()
    }