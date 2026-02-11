# Remote Linux Software Auto-Installer

This project provides a small automation CLI that:

- Connects to a Linux server over SSH.
- Authenticates using either:
  - Username + password, or
  - Username + SSH private key file.
- Lists available software packages for selection.
- Installs selected software non-interactively.

## Supported package managers

The script detects and supports:

- `apt-get` (Debian/Ubuntu)
- `dnf` (modern RHEL/Fedora)
- `yum` (older RHEL/CentOS)
- `zypper` (openSUSE/SLES)

## Software catalog

Current selectable software names:

- `git`
- `curl`
- `wget`
- `vim`
- `htop`
- `docker`
- `nginx`
- `nodejs`
- `python3-pip`

You can extend this list in `SOFTWARE_CATALOG` inside `auto_software_installer.py`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1) Interactive software selection

```bash
python3 auto_software_installer.py \
  --host 192.168.1.10 \
  --username ubuntu \
  --ask-password
```

The tool prints the software list and asks you to choose by number.

### 2) Non-interactive software selection (password auth)

```bash
python3 auto_software_installer.py \
  --host 192.168.1.10 \
  --username ubuntu \
  --ask-password \
  --software git,curl,nginx
```

### 3) Non-interactive software selection (key auth)

```bash
python3 auto_software_installer.py \
  --host 192.168.1.10 \
  --username ubuntu \
  --key-file ~/.ssh/id_rsa \
  --software git,htop
```

## Notes

- The remote user must have `sudo` privileges.
- For key-based auth, non-interactive sudo requires `NOPASSWD` sudo setup on the remote host.
