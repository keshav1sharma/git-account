#!/usr/bin/env python3

import argparse
import os
import json
import re

parser = argparse.ArgumentParser(description='Command Line Utility to manage multiple git accounts')

parser.add_argument('--add', action='store_true', help='Add a new github account')
parser.add_argument('--remove', type=str, help='Remove an existing github account from saved accounts in config')
parser.add_argument(
    "--list", action="store_true", help="List all saved github accounts"
)
parser.add_argument('--set-default', type=str, help='Set a default github account')
parser.add_argument('--get-default', type=str, help='Get the default github account')
parser.add_argument('--use', type=str, help='Use a specific github account')
parser.add_argument('--current', type=str, help='Get the current github account')
parser.add_argument("--update", type=str, help="Update a specific github account config (e.g. ssh key)")
parser.add_argument(
    "--remove-all", action="store_true", help="Clear all saved github accounts"
)


"""
Config File Structure
{
    "alias": {
        "username": "username",
        "email": "email",
        "ssh_key_path": "ssh_key_path"
    }
}

"""

def get_existing_configs():
    # read existing configs from ~/.git-account/config.json
    config_path = os.path.expanduser("~/.git-account/config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            existing_configs = json.load(config_file)
    else:
        #create the config file if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as config_file:
            json.dump({}, config_file, indent=4)
        existing_configs = {}
    return existing_configs

def save_new_config(new_config):
    # save the new configs to ~/.git-account/config.json
    existing_configs = get_existing_configs()
    existing_configs[new_config["alias"]] = {
        "username": new_config["username"],
        "email": new_config["email"],
        "ssh_key_path": new_config["ssh_key_path"],
    }
    config_path = os.path.expanduser("~/.git-account/config.json")
    with open(config_path, "w") as config_file:
        json.dump(existing_configs, config_file, indent=4)

def get_username_list():
    existing_configs = get_existing_configs()
    return [account["username"] for account in existing_configs.values()]

def get_email_list():
    existing_configs = get_existing_configs()
    return [account["email"] for account in existing_configs.values()]

def get_alias_list():
    existing_configs = get_existing_configs()
    return list(existing_configs.keys())

def list_accounts(args):
    list_of_accounts = get_existing_configs()
    if not list_of_accounts:
        print("No saved accounts.")
    else:
        print(json.dumps(list_of_accounts, indent=4))

def add_account(args):
    try:

        username = input("Enter your github username: ")
        if username in get_username_list():
            print("Username already exists. Please choose a different username.")
            return
        email = input("Enter your github email: ")
        email_regex = r"[^@]+@[^@]+\.[^@]+"
        if not re.match(email_regex, email):
            print("Invalid email. Please enter a valid email.")
            return
        if email in get_email_list():
            print("Email already exists. Please choose a different email.")
            return
        alias = input("Enter an alias to use with this account: ")
        if alias in get_alias_list():
            print("Alias already exists. Please choose a different alias.")
            return
        ssh_key_path = ""

        # before this ask if user already have ssh key and pub key in their system
        while True:
            has_ssh_key = (
                input("Do you already have an SSH key? (y/n): ").strip().lower()
            )
            if has_ssh_key in ["y", "n"]:
                if has_ssh_key == "n":
                    break
                # if yes then ask for the path of the key
                if has_ssh_key == "y":
                    existing_ssh_pub_key_path = input("Enter your ssh personal.pub key path: ")
                    existing_ssh_pub_key_path = os.path.expanduser(
                        existing_ssh_pub_key_path
                    )
                    print(f'Existing ssh key path: {existing_ssh_pub_key_path}')
                    is_valid = os.path.exists(
                        existing_ssh_pub_key_path
                    ) and existing_ssh_pub_key_path.endswith(".pub")
                    if is_valid:
                        ssh_key_path = existing_ssh_pub_key_path
                        break
                    else:
                        print("Invalid path. Please enter a valid path.")
            else:            
                print("Invalid choice. Please enter 'y' or 'n'.")

        if ssh_key_path == "":
            ssh_key_path = f"~/.ssh/{alias}.pub"

        new_account = {
            "username": username,
            "email": email,
            "alias": alias,
            "ssh_key_path": ssh_key_path,
        }

        # save the new account to config
        save_new_config(new_account)

        if has_ssh_key == "n":
            # if no existing ssh key then generate ssh key and pub key
            commands = [
                # if ssh folder doesn't exist then create it
                "mkdir -p ~/.ssh",
                "cd ~/.ssh",
                # generate ssh key and pub key
                "pwd",
                f'ssh-keygen -t rsa -C "git-account@{username}" -f ~/.ssh/{alias}',
                # adding keys to apple keychain
                f"ssh-add --apple-use-keychain ~/.ssh/{alias}",
                # copy the pub key to clipboard
                f"pbcopy < {ssh_key_path}",
            ]

            for command in commands:
                os.system(command)

            print("Public ssh key copied to clipboard. Add this key to your github account.")
            print(f'For reference: https://docs.github.com/en/github/authenticating-to-github/adding-a-new-ssh-key-to-your-github-account')

        # add the new configuration into ~/.ssh/config
        with open(os.path.expanduser("~/.ssh/config"), "a") as config_file:
            config_file.write(
                f"\nHost {alias}\n\tHostName github.com\n\tUser git\n\tIdentityFile {ssh_key_path}\n"
            )

        
    except Exception as e:
        print(f"An error occurred: {e}")

def remove_account(args):
    existing_configs = get_existing_configs()
    if args.remove in existing_configs:
        del existing_configs[args.remove]
        config_path = os.path.expanduser("~/.git-account/config.json")
        with open(config_path, "w") as config_file:
            json.dump(existing_configs, config_file, indent=4)
        print(f"Account {args.remove} removed successfully.")
    else:
        print(f"Account {args.remove} not found.")

def remove_all_accounts(args):
    config_path = os.path.expanduser("~/.git-account/config.json")
    os.remove(config_path)
    print("All saved accounts removed successfully.")

def main():

    command_handler = {
        "add": add_account,
        "list": list_accounts,
        "remove": remove_account,
        "remove_all": remove_all_accounts,
    }
    args = parser.parse_args()

    for arg in vars(args):
        if getattr(args, arg):
            if arg in command_handler:
                command_handler[arg](args)
            else:
                print(f"Command {arg} not found. Please check the command and try again.")
            break


if __name__ == '__main__':
    main()
