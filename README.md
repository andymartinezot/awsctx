# `awsctx`: Power tool for AWS CLI profiles

![Latest GitHub release](https://img.shields.io/github/release/andymartinezot/awsctx.svg)
![GitHub stars](https://img.shields.io/github/stars/andymartinezot/awsctx.svg?label=github%20stars)

**awsctx** is a tool to switch between AWS CLI profiles defined in your `~/.aws/config` file — faster.
Think of it as [`kubectx`](https://github.com/ahmetb/kubectx), but for AWS profiles.

[Install &rarr;](#installation)

## What is `awsctx`?

`awsctx` helps you switch between AWS profiles configured in **`~/.aws/config`** quickly
and interactively. It sets `AWS_PROFILE` and `AWS_DEFAULT_REGION` in your shell session
via a lightweight shell hook — no temporary credentials are written, no files are modified.

It works with any profile type in your `~/.aws/config`:
- **SSO profiles** (IAM Identity Center)
- **IAM user profiles** (access key / secret key)
- **Assume-role profiles**
- **SSO session profiles** (refreshable tokens)

### Usage

Switch to another profile that's in `~/.aws/config`:

```sh
$ awsctx my-dev-account
🚀 Switched to: my-dev-account
   Account:  123456789012
   Role:     AdminRole
   Region:   us-east-1
   Session:  7h 42m remaining
```

Switch back to previous profile:

```sh
$ awsctx -
⚡ Switched to: my-prod-account
   Account:  987654321098
   Role:     ReadOnlyRole
   Region:   us-west-2
   Session:  3h 15m remaining
```

List all available profiles with their status:

```sh
$ awsctx --list

AWS Profiles:

  * my-dev-account   (123456789012 | us-east-1)  [7h 42m remaining]
    my-prod-account  (987654321098 | us-west-2)  [3h 15m remaining]
    my-staging       (111222333444 | eu-west-1)  [expired]
```

Show current profile:

```sh
$ awsctx --current
my-dev-account
   Account:  123456789012
   Role:     AdminRole
   Region:   us-east-1
   Session:  7h 41m remaining
```

Switch with a region override:

```sh
$ awsctx my-dev-account -r eu-west-1
```

Set a persistent default region for a profile:

```sh
$ awsctx --set-region us-west-2
```

If you have [`fzf`](https://github.com/junegunn/fzf) installed, you can also
**interactively** select a profile or fuzzy-search by typing a few characters.
To learn more, read [interactive mode &rarr;](#interactive-mode)

-----

## How it works

`awsctx` reads the profiles defined in your **`~/.aws/config`** file — specifically the `[profile ...]` sections — and presents them for selection. When you switch:

1. It sets `AWS_PROFILE` to the selected profile name
2. It sets `AWS_DEFAULT_REGION` to the resolved region
3. All subsequent AWS CLI/SDK commands in that shell use the new profile

For SSO profiles, it also checks `~/.aws/sso/cache/` to show session expiration status (how much time remains before you need to `aws sso login` again).

**No files are modified** — `~/.aws/config` and `~/.aws/credentials` are read-only inputs. The switch happens entirely via environment variables in your shell session.

-----

## Installation

### From source (pip)

```bash
pip install git+https://github.com/andymartinezot/awsctx.git
```

### Development install

```bash
git clone https://github.com/andymartinezot/awsctx.git
cd awsctx
pip install -e .
```

> **Note:** If you get `zsh: command not found: pip`, use `pip3` or the module form instead:
> ```bash
> pip3 install -e .
> # or
> python3 -m pip install -e .
> ```

### Shell hook setup

After installing, activate the shell hook so `awsctx` can export environment variables into your session:

```bash
# Automatic (detects your shell and appends to rc file)
awsctx --setup

# Or manually add to your ~/.zshrc / ~/.bashrc:
eval "$(awsctx --init zsh)"

# For fish:
awsctx --init fish | source
```

-----

### Interactive mode

If you want `awsctx` to present you an interactive menu with fuzzy searching,
you just need to [install `fzf`](https://github.com/junegunn/fzf) in your `$PATH`.

When `fzf` is available, running `awsctx` with no arguments launches the interactive picker automatically. If `fzf` is not installed, a built-in numbered list picker is used as fallback.

-----

### Region priority

When switching profiles, the region is resolved in this order:

1. `-r` / `--region` flag (per-switch override)
2. Per-profile default (set with `--set-region`)
3. `region` field in `~/.aws/config` for that profile
4. Fallback: `us-east-1`

-----

### Prerequisites

- Python 3.8+
- AWS CLI profiles configured in `~/.aws/config`
- (Optional) [`fzf`](https://github.com/junegunn/fzf) for interactive fuzzy search

-----

### Example `~/.aws/config`

`awsctx` works with any standard AWS config. Here's an example with SSO profiles:

```ini
[profile dev]
sso_session = my-sso
sso_account_id = 123456789012
sso_role_name = AdminRole
region = us-east-1

[profile staging]
sso_session = my-sso
sso_account_id = 111222333444
sso_role_name = AdminRole
region = eu-west-1

[profile prod]
sso_session = my-sso
sso_account_id = 987654321098
sso_role_name = ReadOnlyRole
region = us-west-2

[sso-session my-sso]
sso_start_url = https://my-org.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

-----

### Inspired by

- [`kubectx`](https://github.com/ahmetb/kubectx) — the original context switcher for Kubernetes
