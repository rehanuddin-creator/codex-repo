#!/usr/bin/env python3
"""Automated Linux software installer over SSH.

Features:
- SSH authentication with password or private key
- Built-in software catalog users can select from
- Non-interactive package installation on Debian/Ubuntu, RHEL-family, and openSUSE
"""

from __future__ import annotations

import argparse
import getpass
import shlex
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

try:
    import paramiko
except ImportError:  # pragma: no cover - handled at runtime when executing app
    paramiko = None


SOFTWARE_CATALOG: Dict[str, str] = {
    "git": "git",
    "curl": "curl",
    "wget": "wget",
    "vim": "vim",
    "htop": "htop",
    "docker": "docker.io",
    "nginx": "nginx",
    "nodejs": "nodejs",
    "python3-pip": "python3-pip",
}


@dataclass
class SSHConfig:
    host: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    port: int = 22


class RemoteInstallerError(RuntimeError):
    pass


class RemoteInstaller:
    def __init__(self, ssh_config: SSHConfig, timeout: int = 20) -> None:
        if paramiko is None:
            raise RemoteInstallerError(
                "paramiko is required. Install dependencies with: pip install -r requirements.txt"
            )

        self.ssh_config = ssh_config
        self.timeout = timeout
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self) -> None:
        kwargs = {
            "hostname": self.ssh_config.host,
            "username": self.ssh_config.username,
            "port": self.ssh_config.port,
            "timeout": self.timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if self.ssh_config.key_file:
            kwargs["key_filename"] = self.ssh_config.key_file
        else:
            kwargs["password"] = self.ssh_config.password

        self.client.connect(**kwargs)

    def close(self) -> None:
        self.client.close()

    def run(self, command: str) -> str:
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if exit_code != 0:
            raise RemoteInstallerError(
                f"Command failed (exit={exit_code}): {command}\nSTDERR: {err}\nSTDOUT: {out}"
            )
        return out

    def detect_package_manager(self) -> str:
        cmd = """bash -lc 'if command -v apt-get >/dev/null 2>&1; then echo apt; \
elif command -v dnf >/dev/null 2>&1; then echo dnf; \
elif command -v yum >/dev/null 2>&1; then echo yum; \
elif command -v zypper >/dev/null 2>&1; then echo zypper; \
else echo unknown; fi'"""
        manager = self.run(cmd)
        if manager == "unknown":
            raise RemoteInstallerError("Unsupported Linux distribution: no known package manager found.")
        return manager

    def build_install_command(self, package_manager: str, packages: Sequence[str]) -> str:
        quoted_packages = " ".join(shlex.quote(pkg) for pkg in packages)
        if package_manager == "apt":
            install_cmd = f"DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {quoted_packages}"
        elif package_manager in {"dnf", "yum"}:
            install_cmd = f"{package_manager} install -y {quoted_packages}"
        elif package_manager == "zypper":
            install_cmd = f"zypper --non-interactive install {quoted_packages}"
        else:
            raise RemoteInstallerError(f"Unsupported package manager: {package_manager}")

        if self.ssh_config.password:
            escaped_password = shlex.quote(self.ssh_config.password)
            return f"bash -lc \"echo {escaped_password} | sudo -S bash -lc {shlex.quote(install_cmd)}\""
        return f"sudo -n bash -lc {shlex.quote(install_cmd)}"

    def install(self, software_names: Sequence[str]) -> None:
        if not software_names:
            raise RemoteInstallerError("No software selected for installation.")

        manager = self.detect_package_manager()
        packages = [SOFTWARE_CATALOG[name] for name in software_names]
        command = self.build_install_command(manager, packages)
        self.run(command)


def parse_selection(raw_selection: str, total_options: int) -> List[int]:
    picked: List[int] = []
    for token in raw_selection.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            raise ValueError(f"Invalid selection '{token}'. Use numbers separated by commas.")
        idx = int(token)
        if idx < 1 or idx > total_options:
            raise ValueError(f"Selection out of range: {idx}. Valid range is 1-{total_options}.")
        if idx not in picked:
            picked.append(idx)
    return picked


def interactive_software_choice() -> List[str]:
    options = list(SOFTWARE_CATALOG.keys())
    print("Available software:")
    for i, name in enumerate(options, start=1):
        print(f"  {i}. {name}")

    raw = input("Select software by number (comma-separated, e.g. 1,3,5): ").strip()
    indices = parse_selection(raw, len(options))
    if not indices:
        raise ValueError("No software selected.")
    return [options[i - 1] for i in indices]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install selected software on a remote Linux server through SSH."
    )
    parser.add_argument("--host", required=True, help="Remote server hostname or IP")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--username", required=True, help="SSH username")

    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--password", help="SSH password")
    auth.add_argument("--key-file", help="Path to private key file for SSH auth")

    parser.add_argument(
        "--software",
        help=(
            "Comma-separated software names from the catalog "
            f"({', '.join(SOFTWARE_CATALOG.keys())}). If omitted, interactive menu is shown."
        ),
    )
    parser.add_argument(
        "--ask-password",
        action="store_true",
        help="Prompt securely for SSH password instead of passing --password in shell history.",
    )

    return parser.parse_args(argv)


def resolve_software_list(software_arg: Optional[str]) -> List[str]:
    if not software_arg:
        return interactive_software_choice()

    requested = [item.strip() for item in software_arg.split(",") if item.strip()]
    if not requested:
        raise ValueError("--software provided but no valid entries were found.")

    invalid = [name for name in requested if name not in SOFTWARE_CATALOG]
    if invalid:
        valid = ", ".join(SOFTWARE_CATALOG.keys())
        raise ValueError(f"Unknown software names: {', '.join(invalid)}. Valid options: {valid}")

    unique: List[str] = []
    for item in requested:
        if item not in unique:
            unique.append(item)
    return unique


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    password = args.password
    if args.ask_password:
        password = getpass.getpass("SSH password: ")

    try:
        software_names = resolve_software_list(args.software)
        config = SSHConfig(
            host=args.host,
            username=args.username,
            password=password,
            key_file=args.key_file,
            port=args.port,
        )

        installer = RemoteInstaller(config)
        installer.connect()
        try:
            installer.install(software_names)
        finally:
            installer.close()

        print("Installation completed successfully for:", ", ".join(software_names))
        return 0
    except (RemoteInstallerError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
