# Remote Linux Software Auto-Installer

This project provides automation that:

- Connects to a Linux server over SSH.
- Authenticates using either:
  - Username + password, or
  - Username + SSH private key file.
- Lists available software packages for selection.
- Installs selected software non-interactively.
- Can run as:
  - a local CLI, and
  - a Google Cloud Function HTTP endpoint.

## Google Cloud Function compatibility

Yes, this project is compatible with Google Cloud Functions (2nd gen) and Cloud Run functions.

### Important deployment note

If you use key-based authentication, your key file must be available in the function runtime (for example via Secret Manager mounted as a file).

### Deploy command example

```bash
gcloud functions deploy install-software \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point install_software_http \
  --trigger-http \
  --allow-unauthenticated
```

### HTTP request payload example

```json
{
  "host": "10.0.0.5",
  "username": "ubuntu",
  "password": "your-ssh-password",
  "port": 22,
  "software": ["git", "curl", "nginx"]
}
```

For key auth use `key_file` instead of `password`:

```json
{
  "host": "10.0.0.5",
  "username": "ubuntu",
  "key_file": "/workspace/secrets/id_rsa",
  "software": ["git", "htop"]
}
```

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

## CLI Usage

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
- For production use in GCP, secure credentials with Secret Manager and restrict who can invoke the HTTP function.
