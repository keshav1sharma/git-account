# Git Account Manager

A command line utility to manage multiple GitHub accounts efficiently. This tool helps developers switch between different GitHub accounts seamlessly, manage SSH keys, and maintain separate configurations for each account.

## Installation

```bash
pip install gitaccount
```

## Features

- Add and manage multiple GitHub accounts
- Switch between different GitHub accounts
- Set default GitHub account
- Automatic SSH key generation and management
- List all configured accounts
- Remove specific or all accounts

## Commands

### Add a New Account
```bash
gitaccount --add
```
This interactive command will:
- Prompt for GitHub username and email
- Create an alias for the account
- Generate or use existing SSH keys
- Automatically copy public key to clipboard
- Configure SSH settings

### List All Accounts
```bash
gitaccount --list
```
Displays all configured accounts with their details.

### Switch Between Accounts
```bash
gitaccount --switch work-account
```
Switches Git configuration to use the specified account for the current repository.

### Set Default Account
```bash
gitaccount --set-default personal-account
```
Sets the global Git configuration to use the specified account.

### Show Current Account
```bash
gitaccount --current
```
Displays the currently active Git account.

### Remove an Account
```bash
gitaccount --remove work-account
```
Removes the specified account configuration and its SSH settings.

### Remove All Accounts
```bash
gitaccount --remove-all
```
Clears all saved accounts and configurations.

## Configuration

- Configurations are stored in `~/.git-account/config.json`
- SSH configurations are managed in `~/.ssh/config`
- SSH keys are stored in `~/.ssh/` directory

## License

MIT License

## Author

Keshav Sharma