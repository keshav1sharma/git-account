#!/usr/bin/env python3
"""
Git Account Manager - A command line utility to manage multiple GitHub accounts.

This tool allows users to:
- Add and remove GitHub accounts
- Switch between different GitHub accounts
- Set default GitHub account
- List all configured accounts
- Manage SSH keys for different accounts

The configuration is stored in ~/.git-account/config.json and SSH configurations
are managed in ~/.ssh/config.
"""

import argparse
import os
import json
import re
import subprocess
from typing import Dict, List
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitAccountConfigError(Exception):
    """Custom exception for Git account configuration errors."""
    def __init__(self, message: str, error_code: int = None):
        """
        Initialize the exception with a message and optional error code.

        Args:
            message (str): Error message describing what went wrong
            error_code (int, optional): Numeric code identifying the error type
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class GitAccountManager:
    """
    Main class for managing multiple Git accounts.

    This class handles all operations related to managing multiple Git accounts
    including configuration storage, SSH key management, and Git configurations.

    Attributes:
        CONFIG_DIR (Path): Path to the configuration directory
        CONFIG_FILE (Path): Path to the configuration file
        SSH_CONFIG_FILE (Path): Path to the SSH config file
    """

    CONFIG_DIR = Path.home() / ".git-account"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    SSH_CONFIG_FILE = Path.home() / ".ssh" / "config"

    def __init__(self):
        """Initialize the GitAccountManager and ensure required directories exist."""
        self._ensure_config_directory()

    def _ensure_config_directory(self) -> None:
        """Create configuration directory and file if they don't exist."""
        self.CONFIG_DIR.mkdir(exist_ok=True)
        if not self.CONFIG_FILE.exists():
            self.CONFIG_FILE.write_text("{}")

    def get_configs(self) -> Dict:
        """
        Read and return existing configurations.

        Returns:
            Dict: Dictionary containing all configured Git accounts

        Raises:
            GitAccountConfigError: If config file cannot be read or parsed
        """
        try:
            return json.loads(self.CONFIG_FILE.read_text())
        except json.JSONDecodeError as e:
            raise GitAccountConfigError(f"Invalid config file format: {e}")
        except IOError as e:
            raise GitAccountConfigError(f"Could not read config file: {e}")

    def save_config(self, config: Dict) -> None:
        """
        Save configuration to file.

        Args:
            config (Dict): Configuration dictionary to save

        Raises:
            GitAccountConfigError: If config cannot be saved
        """
        try:
            self.CONFIG_FILE.write_text(json.dumps(config, indent=4))
        except IOError as e:
            raise GitAccountConfigError(f"Could not save config: {e}")

    def get_usernames(self) -> List[str]:
        """Return list of configured usernames."""
        configs = self.get_configs()
        return [account["username"] for account in configs.values()]

    def get_emails(self) -> List[str]:
        """Return list of configured email addresses."""
        configs = self.get_configs()
        return [account["email"] for account in configs.values()]

    def get_aliases(self) -> List[str]:
        """Return list of configured aliases."""
        return list(self.get_configs().keys())

    def validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email (str): Email address to validate

        Returns:
            bool: True if email is valid, False otherwise
        """
        email_regex = r"[^@]+@[^@]+\.[^@]+"
        return bool(re.match(email_regex, email))

    def update_ssh_config(self, alias: str, ssh_key_path: str) -> None:
        """
        Update SSH configuration for an account.

        Args:
            alias (str): Account alias
            ssh_key_path (str): Path to SSH key

        Raises:
            GitAccountConfigError: If SSH config cannot be updated
        """
        try:
            config_entry = (
                f"\nHost {alias}\n"
                f"\tHostName github.com\n"
                f"\tUser git\n"
                f"\tIdentityFile {ssh_key_path}\n"
            )
            with open(self.SSH_CONFIG_FILE, "a") as f:
                f.write(config_entry)
        except IOError as e:
            raise GitAccountConfigError(f"Failed to update SSH config: {e}")

    def remove_ssh_config_entry(self, alias: str) -> None:
        """
        Remove SSH configuration entry for an account.

        Args:
            alias (str): Account alias to remove

        Raises:
            GitAccountConfigError: If SSH config cannot be modified
        """
        try:
            if not self.SSH_CONFIG_FILE.exists():
                return

            lines = self.SSH_CONFIG_FILE.read_text().splitlines(True)
            with open(self.SSH_CONFIG_FILE, "w") as f:
                skip_lines = False
                for line in lines:
                    if line.strip().startswith(f"Host {alias}"):
                        skip_lines = True
                        continue
                    if skip_lines and (
                        line.strip().startswith("Host ") or not line.strip()
                    ):
                        skip_lines = False
                    if not skip_lines:
                        f.write(line)
        except IOError as e:
            raise GitAccountConfigError(f"Failed to remove SSH config entry: {e}")

    def update_git_remote_origin(self, alias: str) -> None:
        """
        Update Git remote origin URL for the current repository.

        Args:
            alias (str): Account alias to use

        Raises:
            GitAccountConfigError: If Git commands fail
        """
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()
            match = re.search(r"[:/]([^/:]+)/([^/]+)\.git$", remote_url)
            if not match:
                raise GitAccountConfigError("Failed to parse remote URL, not a valid Git repo")

            username, repo = match.groups()
            new_origin_url = f"git@{alias}:{username}/{repo}.git"

            subprocess.run(["git", "remote", "rm", "origin"], check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", new_origin_url], check=True
            )
            subprocess.run(
                ["git", "remote", "set-url", "origin", new_origin_url], check=True
            )
        except subprocess.CalledProcessError as e:
            raise GitAccountConfigError(f"Git command failed: {e}")

    def update_git_config(self, alias: str, is_global: bool = False) -> None:
        """
        Update Git configuration for an account.

        Args:
            alias (str): Account alias
            is_global (bool): Whether to update global Git config

        Raises:
            GitAccountConfigError: If Git config cannot be updated
        """
        try:
            configs = self.get_configs()
            if alias not in configs:
                raise GitAccountConfigError(f"Account {alias} not found")

            config = configs[alias]
            git_config_cmd = ["git", "config"]
            if is_global:
                git_config_cmd.append("--global")

            subprocess.run(
                [*git_config_cmd, "user.name", config["username"]], check=True
            )
            subprocess.run([*git_config_cmd, "user.email", config["email"]], check=True)
            subprocess.run(
                [*git_config_cmd, "user.signingkey", config["ssh_key_path"]], check=True
            )
        except subprocess.CalledProcessError as e:
            raise GitAccountConfigError(f"Failed to update Git config: {e}")

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Command Line Utility to manage multiple git accounts"
    )
    parser.add_argument("--add", action="store_true", help="Add a new github account")
    parser.add_argument("--remove", type=str, help="Remove an existing github account")
    parser.add_argument(
        "--list", action="store_true", help="List all saved github accounts"
    )
    parser.add_argument("--set-default", type=str, help="Set a default github account")
    parser.add_argument(
        "--switch", type=str, help="Switch to a specific github account"
    )
    parser.add_argument("--current", action="store_true", help="Show current github account")
    parser.add_argument(
        "--remove-all", action="store_true", help="Clear all saved github accounts"
    )
    return parser

def handle_add_account(manager: GitAccountManager) -> None:
    """Handle adding a new Git account."""
    try:
        username = input("Enter your GitHub username: ")
        if username in manager.get_usernames():
            raise GitAccountConfigError("Username already exists")

        email = input("Enter your GitHub email: ")
        if not manager.validate_email(email):
            raise GitAccountConfigError("Invalid email format")
        if email in manager.get_emails():
            raise GitAccountConfigError("Email already exists")

        alias = input("Enter an alias for this account: ")
        if alias in manager.get_aliases():
            raise GitAccountConfigError("Alias already exists")

        has_ssh_key = input("Do you already have an SSH key? (y/n): ").strip().lower()
        ssh_key_path = ""

        if has_ssh_key == "y":
            ssh_key_path = input("Enter your SSH public key path: ")
            ssh_key_path = os.path.expanduser(ssh_key_path)
            if not Path(ssh_key_path).exists() or not ssh_key_path.endswith(".pub"):
                raise GitAccountConfigError("Invalid SSH key path")
        else:
            ssh_key_path = f"~/.ssh/{alias}.pub"
            logger.info("Generating new SSH key...")

            # Create .ssh directory if it doesn't exist
            ssh_dir = Path.home() / ".ssh"
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

            # Generate SSH key
            key_path = os.path.expanduser(f"~/.ssh/{alias}")
            subprocess.run(
                [
                    "ssh-keygen",
                    "-t",
                    "rsa",
                    "-C",
                    f"git-account@{username}",
                    "-f",
                    key_path,
                ],
                check=True,
            )

            # Add to keychain
            logger.info("Adding SSH key to keychain...")
            subprocess.run(["ssh-add", "--apple-use-keychain", key_path], check=True)

            # Copy to clipboard using pbcopy
            logger.info("Copying public key to clipboard...")
            with open(f"{key_path}.pub", "r") as pub_key:
                subprocess.run(["pbcopy"], input=pub_key.read().encode(), check=True)
            print("Public SSH key has been copied to clipboard.")
            print("Please add it to your GitHub account: https://github.com/settings/keys")

        logger.info("Saving configuration...")
        configs = manager.get_configs()
        configs[alias] = {
            "username": username,
            "email": email,
            "ssh_key_path": ssh_key_path,
        }
        manager.save_config(configs)
        manager.update_ssh_config(alias, ssh_key_path)

        print("\nAccount setup completed successfully!")

    except (GitAccountConfigError, subprocess.CalledProcessError) as e:
        logger.error(f"Failed to add account: {str(e)}")
        raise

def main():
    """Main entry point for the Git account manager."""
    parser = create_argument_parser()
    args = parser.parse_args()
    manager = GitAccountManager()

    try:
        if args.add:
            handle_add_account(manager)
        elif args.list:
            configs = manager.get_configs()
            if not configs:
                print("No saved accounts.")
            else:
                print(json.dumps(configs, indent=4))
        elif args.remove:
            configs = manager.get_configs()
            if args.remove in configs:
                del configs[args.remove]
                manager.save_config(configs)
                manager.remove_ssh_config_entry(args.remove)
                print(f"Account {args.remove} removed successfully")
            else:
                print(f"Account {args.remove} not found")
        elif args.remove_all:
            manager.CONFIG_FILE.unlink(missing_ok=True)
            manager.SSH_CONFIG_FILE.unlink(missing_ok=True)
            manager._ensure_config_directory
            print("All saved accounts removed successfully")
        elif args.switch:
            manager.update_git_config(args.switch)
            manager.update_git_remote_origin(args.switch)
            print(f"Switched to account {args.switch}")
        elif args.set_default:
            manager.update_git_config(args.set_default, is_global=True)
            print(f"Default account set to {args.set_default}")
        elif args.current:
            result = subprocess.run(
                ["git", "config", "--get", "user.name"],
                capture_output=True,
                text=True,
            )
            username = result.stdout.strip()
            print(f"Current account: {username}")
        else:
            parser.print_help()
    except (GitAccountConfigError, subprocess.CalledProcessError) as e:
        logger.error(str(e))
        exit(1)

if __name__ == "__main__":
    main()
