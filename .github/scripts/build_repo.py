#!/usr/bin/env python3

import argparse
import json
import urllib.request
import sys
import os
import subprocess
from email.utils import formatdate

GITHUB_BASE_API = "https://api.github.com/repos"

DEFAULT_GPG_FINGERPRINT = "5277E8C721237125"
DEFAULT_OUTPUT_DIR = "ubuntu"
DEFAULT_PKG_LIST = ".github/config/package_list.txt"

GITHUB_NAMESPACE = "kowabunga-cloud"
GITHUB_PROJECTS = ["kowabunga", "koala"]

REPO_DISTS = ["noble"]
REPO_COMPONENT = "main"

# main
if __name__ == "__main__":
    # parse command-line
    ps = argparse.ArgumentParser()
    ps.add_argument('-o', '--output', action='store', default=DEFAULT_OUTPUT_DIR, help='Packages repository output directory')
    ps.add_argument('-c', '--config', action='store', default=DEFAULT_PKG_LIST, help='gitHub repositories to pull packages from releases')
    ps.add_argument('-f', '--fingerprint', action='store', default=DEFAULT_GPG_FINGERPRINT, help='GPG Fingerprint to sign with')
    ps.add_argument('-p', '--passphrase', action='store', default='', help='GPG Passphrase to decrypt key')
    args = ps.parse_args()

    with open(args.config, 'r') as f:
        projects = f.read().splitlines()

    architectures = set()

    # download deb packages into pool
    for p in projects:
        releases_url = f'{GITHUB_BASE_API}/{p}/releases'
        request = urllib.request.urlopen(releases_url)
        releases = json.loads(request.read())
        for r in releases:
            assets = r.get('assets')
            for a in assets:
                filename = a.get('name')
                if not filename.endswith(".deb"):
                    continue
                arch = filename.split('_')[-1].split('.')[0]
                architectures.add(arch)
                debfile = a.get('browser_download_url')
                pool = f'{args.output}/pool/main'
                if not os.path.isdir(pool):
                    os.makedirs(pool, exist_ok=True)
                dst = f'{pool}/{filename}'
                if not os.path.isfile(dst):
                    print(f'Downloading {filename} from {debfile} into {dst}')
                    urllib.request.urlretrieve(debfile, dst)


    # build up repository
    for d in REPO_DISTS:
        os.chdir(args.output)
        for arch in architectures:
            component = f'dists/{d}/{REPO_COMPONENT}'
            bindir = f'{component}/binary-{arch}'
            if not os.path.isdir(bindir):
                os.makedirs(bindir, exist_ok=True)
            os.system(f'dpkg-scanpackages --arch {arch} --multiversion pool > {bindir}/Packages')
            os.system(f'gzip -9 > {bindir}/Packages.gz < {bindir}/Packages')
            os.system(f'xz -9 > {bindir}/Packages.xz < {bindir}/Packages')
            if os.path.exists(f'{bindir}/Packages'):
                os.remove(f'{bindir}/Packages')

            release = f'''Origin: Kowabunga
Label: Kowabunga
Version: 1.0
Acquire-By-Hash: no
Component: {REPO_COMPONENT}
Architecture: {arch}
'''
            with open(f'{bindir}/Release', "w") as f:
                f.write(release)

        os.chdir(f'dists/{d}')
        md5sums = []
        sha1sums = []
        sha256sums = []
        sha512sums = []
        for root, dirs, files in os.walk(REPO_COMPONENT):
            for filename in files:
                fname = os.path.join(root, filename)
                wc = os.popen(f'wc -c "{fname}"').read().replace('\n', '')
                md5 = os.popen(f'md5sum "{fname}" | cut -d " " -f 1').read().replace('\n', '')
                md5sums.append(f' {md5} {wc}')
                sha1 = os.popen(f'sha1sum "{fname}" | cut -d " " -f 1').read().replace('\n', '')
                sha1sums.append(f' {sha1} {wc}')
                sha256 = os.popen(f'sha256sum "{fname}" | cut -d " " -f 1').read().replace('\n', '')
                sha256sums.append(f' {sha256} {wc}')
                sha512 = os.popen(f'sha512sum "{fname}" | cut -d " " -f 1').read().replace('\n', '')
                sha512sums.append(f' {sha512} {wc}')
        release = f'''Origin: Kowabunga
Label: Kowabunga
Suite: stable
Codename: {d}
Version: 1.0
Architectures: {' '.join(architectures)}
Components: {REPO_COMPONENT}
Description: Kowabunga Ubuntu Packages Repository
Date: {formatdate()}
MD5Sum:
{'\n'.join(md5sums)}
SHA1:
{'\n'.join(sha1sums)}
SHA256:
{'\n'.join(sha256sums)}
SHA512:
{'\n'.join(sha512sums)}
'''
        with open('Release', "w") as f:
            f.write(release)

        os.system(f'gpg --default-key "{args.fingerprint}" -abs --batch --pinentry-mode loopback --passphrase \'{args.passphrase}\' -o - Release > Release.gpg')
        os.system(f'gpg --default-key "{args.fingerprint}" --clearsign --batch --pinentry-mode loopback --passphrase \'{args.passphrase}\' -o - Release > InRelease')

sys.exit(0)
