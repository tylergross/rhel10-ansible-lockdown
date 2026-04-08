# rhel10-lockdown

Ansible-based framework for applying DISA STIG hardening controls to Red Hat Enterprise Linux 10.

---

## Overview

This project automates the enforcement of the **RHEL 10 STIG V1R1** (Benchmark Date: 26 Feb 2026) as published by DISA. Each STIG control is implemented as an individual, toggle-able task within the `rhel10-stig` Ansible role, allowing granular control over which checks are enforced.

**Total controls:** 434 (all implemented)

| Severity | Count |
|----------|-------|
| HIGH     | 30    |
| MEDIUM   | 399   |
| LOW      | 5     |

---

## Repository Structure

```
rhel10-lockdown/
├── inventory/
│   └── hosts.yml              # Target host inventory
├── roles/
│   └── rhel10-stig/           # Core STIG hardening role
│       ├── defaults/
│       │   └── main.yml       # All control toggles (default: true/enabled)
│       ├── handlers/
│       │   └── main.yml       # Service restart and reload handlers
│       ├── meta/
│       │   └── main.yml       # Role metadata
│       ├── tasks/
│       │   ├── main.yml       # Includes all individual STIG task files
│       │   └── rhel-10-*.yml  # One file per STIG control (434 total)
│       └── vars/
│           └── main.yml       # Local overrides (takes precedence over defaults)
├── site.yml                   # Main playbook entry point
├── enforce.sh                 # Convenience wrapper for running the playbook
├── customize.py               # Interactive CLI for toggling STIG controls
├── README.md                  # This file
└── CHANGELOG.md               # Version history
```

---

## Prerequisites

- Ansible >= 2.14
- Python >= 3.9 on the control node
- SSH access to target RHEL 10 hosts with a user that can `become` root
- Target hosts must be running **Red Hat Enterprise Linux 10**

---

## Quick Start

### 1. Configure your inventory

Edit `inventory/hosts.yml` and add your target hosts under the `rhel10` group:

```yaml
all:
  children:
    rhel10:
      hosts:
        my-server:
          ansible_host: 192.168.1.100
          ansible_user: ansible
```

### 2. Run all controls (check mode first — recommended)

```bash
# Dry run — no changes applied
./enforce.sh --check

# Apply all controls
./enforce.sh
```

### 3. Run specific severity levels

```bash
# High severity only
./enforce.sh --tags high

# High and medium
./enforce.sh --tags high,medium
```

### 4. Run a specific STIG control

```bash
./enforce.sh --tags RHEL-10-700970
```

---

## Customizing Controls

### Interactive CLI (recommended)

`customize.py` provides a full-screen terminal UI for reviewing and toggling controls before running the playbook. It requires no extra packages — only the Python 3 standard library included with RHEL 10.

```bash
python3 customize.py
```

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate the list |
| `PgUp` / `PgDn` | Page through controls |
| `Space` | Toggle control on / off |
| `i` or `Enter` | View full description, check text, and fix text |
| `f` | Cycle severity filter: ALL → HIGH → MEDIUM → LOW |
| `/` | Search by STIG ID or title keyword |
| `s` | Save overrides to `vars/main.yml` |
| `q` | Quit (prompts if there are unsaved changes) |

Saves only values that differ from the defaults, keeping `vars/main.yml` minimal.

### Manual Override

All controls are **enabled by default**. To skip a specific control, add its variable to `roles/rhel10-stig/vars/main.yml`:

```yaml
# roles/rhel10-stig/vars/main.yml

# Disable debug-shell STIG check
rhel_10_700970: false
```

All available control variable names are listed in `roles/rhel10-stig/defaults/main.yml` with their corresponding STIG ID, severity, and title.

---

## Adding Custom Roles

To add additional hardening roles beyond the STIG baseline:

1. Create a new role under `roles/`:
   ```bash
   mkdir -p roles/my-custom-role/{tasks,handlers,vars,defaults,meta}
   ```
2. Add the role to `site.yml`:
   ```yaml
   roles:
     - role: rhel10-stig
     - role: my-custom-role
   ```

---

## Tags Reference

Each task is tagged with:
- **STIG ID** — e.g., `RHEL-10-700970`
- **Severity** — `high`, `medium`, or `low`
- **CCI** — e.g., `CCI-002235`

```bash
# Run by tag examples
ansible-playbook -i inventory/hosts.yml site.yml --tags RHEL-10-700970
ansible-playbook -i inventory/hosts.yml site.yml --tags high
ansible-playbook -i inventory/hosts.yml site.yml --tags CCI-002235
ansible-playbook -i inventory/hosts.yml site.yml --skip-tags low
```

---

## Author

**Tyler Gross**
[TGTechAcademy.com](https://TGTechAcademy.com)

---

## Reference

- [DISA STIG Library](https://public.cyber.mil/stigs/)
- RHEL 10 STIG V1R1 — Benchmark Date: 26 Feb 2026
- [Ansible Documentation](https://docs.ansible.com/)
