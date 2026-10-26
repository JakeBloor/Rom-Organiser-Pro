"""A fake EmuMovies file server for tests: folders, files, and a record of anything that tried to change them."""

import ftplib
from collections import Counter


class FakeServer:
    """What the fake FTP connections see: folders, files, and anything that tried to change them."""

    def __init__(self):
        self.tree = {"": ["Official", "Submissions"], "Official": []}
        self.files = {}
        self.listed = Counter()
        self.downloaded = []
        self.changes = []
        self.unlistable = set()
        self.download_error = None
        self.refuse_tls = False
        self.wrong_password = False
        self.gone = False
        self.down_hosts = set()


class FakeFTP:
    tls = False
    server = None

    def __init__(self, host, timeout=None):
        if host in self.server.down_hosts:
            raise OSError(f"{host} can't be reached")
        self.host = host

    def login(self, user, password):
        if self.server.wrong_password:
            raise ftplib.error_perm("530 Login incorrect")
        if self.tls and self.server.refuse_tls:
            raise ftplib.error_perm("534 TLS not available")

    def prot_p(self):
        pass

    def nlst(self, path):
        self.server.listed[path] += 1
        if path in self.server.unlistable:
            raise ftplib.error_perm("550 No such folder")
        return [f"{path}/{name}" for name in self.server.tree.get(path, [])]

    def retrbinary(self, command, callback):
        if self.server.download_error:
            callback(b"partial")
            raise OSError(self.server.download_error)
        path = command[len("RETR "):]
        self.server.downloaded.append(path)
        callback(self.server.files[path])

    def size(self, path):
        return len(self.server.files[path])

    # Anything that would change the server; the read-only guard must stop these first
    def delete(self, name):
        self.server.changes.append(("delete", name))

    def storbinary(self, command, file):
        self.server.changes.append(("upload", command))

    def rename(self, old, new):
        self.server.changes.append(("rename", old))

    def mkd(self, name):
        self.server.changes.append(("mkd", name))

    def rmd(self, name):
        self.server.changes.append(("rmd", name))

    def sendcmd(self, command):
        self.server.changes.append(("sendcmd", command))

    def quit(self):
        if self.server.gone:
            raise OSError("connection closed")

    def close(self):
        pass


class FakeFTPTLS(FakeFTP):
    tls = True
