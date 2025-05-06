---
layout: home
title: Ubuntu APT Repository for Kowabunga
---
This allows you to install Kowabunga on Ubuntu LTS distributions.

Currently support Ubuntu edition are:

- **noble** (24.04)

## GPG Keyring

Kowabunga packages are digitally signed using GPG. Public key can be imported the following way:

```
wget -qO- {{ site.url }}/kowabunga.asc | sudo tee /etc/apt/keyrings/kowabunga.asc >/dev/null
```

## APT Repository

Adding **Kowabunga** APT repository can be achieved by creating the **/etc/apt/sources.list.d/kowabunga.sources** file with associated content:

```
Enabled: yes
Types: deb
URIs: http://packages.kowabunga.cloud/ubuntu
Suites: noble
Components: main
Signed-By: /etc/apt/keyrings/kowabunga.asc
```

Then run `apt update && apt install -y` followed by the names of the packages you want to install.
