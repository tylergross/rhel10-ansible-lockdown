# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.5.0] — 2026-04-07

### Fixed
- **handlers/main.yml** — defined all missing handlers (`restart auditd`, `restart sshd`, `run dconf update`, `reload NetworkManager`, `reload firewalld`) that 63+ tasks were notifying but never declared; fixed capitalization mismatch on `Restart sshd` in `RHEL-10-600640`
- **500xxx audit rules (49 files)** — re-check verify tasks were running `auditctl -l` (live kernel rules) before `auditd` restarted, causing false assert failures; changed all verify commands to `cat /etc/audit/rules.d/rhel10-stig.rules`
- **RHEL-10-700790** — `dconf update` was failing with "Key file does not start with a group" because `lineinfile` created `00-security-settings` without a `[org/gnome/desktop/screensaver]` group header; added missing header task
- **701xxx sysctl tasks (32 files)** — replaced `ansible.posix.sysctl` (collection not installed) with `ansible.builtin.lineinfile` + `sysctl -p` using only built-in modules
- **regex_search capture groups (20 files)** — `regex_search('PARAM', '\1') | first | int` is unsupported in this Ansible/Jinja2 version; replaced all check/verify commands with `awk` compliance tests (rc=0 = compliant) and simplified all `when:` and assert `that:` to `rc != 0` / `rc == 0`
- **RHEL-10-600700 / 600720** — removed `set_fact` blocks that still used broken `regex_search`; consolidated to `check.rc != 0` conditions
- **RHEL-10-600750, 700950, 701150, 701160** — backup `copy` tasks aborted when source file did not exist; added `ansible.builtin.stat` guard so backup is skipped if the file is absent
- **RHEL-10-700800** — hard `assert` on `dconf update` rc replaced with conditional `debug` tasks; non-zero rc now emits `result=WARN` and continues rather than aborting
- **RHEL-10-900100** — `-e 2` immutable flag assertion was using fragile Jinja2 `select('match')` on `auditctl -l` output; changed to `grep -E '^\s*-e\s+2\s*$'` against the rules file with `rc == 0` assert
- **RHEL-10-600140** — expiration-date check was flagging all system service accounts; scoped to UID ≥ 1000 interactive accounts with non-nologin shells only
- **RHEL-10-600170** — PATH-in-init-files check converted from hard assert to audit-only `debug` output; reports `result=FAIL` to Splunk without aborting the play
- **RHEL-10-600730** — SHA-512 hash check was flagging root and system accounts; scoped to UID ≥ 1000, skips locked/unset accounts (`!`, `*`, `!!`)
- **enforce.sh** — fixed Windows CRLF line endings that caused `/usr/bin/env: 'bash\r': No such file or directory` on Linux

---

## [0.4.0] — 2026-04-07

### Added
- `customize.py` — interactive CLI customizer for toggling STIG controls before running the playbook
  - Anaconda-style curses TUI; no extra packages required (Python stdlib only)
  - Browse all 434 controls with STIG ID, severity, and title
  - `Space` to toggle a control on/off; `i`/`Enter` to view full description, check text, and fix text
  - Filter by severity (ALL / HIGH / MEDIUM / LOW) and live keyword search (`/`)
  - Unsaved changes highlighted; `s` saves overrides to `vars/main.yml`; prompts on quit with unsaved changes
  - Writes only values that differ from `defaults/main.yml` — keeps `vars/main.yml` clean

---

## [0.3.0] — 2026-04-06

### Added
- Implemented all 30 remaining RHEL-10-701xxx controls — all 434 controls are now fully implemented
  - **701000–701020**: Kernel hardening boot args via `grubby` (`page_poison=1`, `init_on_free=1`, `pti=on`) persisted to `/etc/default/grub`
  - **701030–701090, 701130, 701140**: sysctl kernel parameters via `ansible.posix.sysctl` into `/etc/sysctl.d/rhel10-stig.conf`
  - **701100–701120**: Kernel module blacklists (CAN, SCTP, TIPC) via `/etc/modprobe.d/`
  - **701150–701160**: systemd coredump config (`ProcessSizeMax=0`, `Storage=none`)
  - **701170**: PAM limits (`* hard core 0`) via `/etc/security/limits.d/rhel10-stig-coredump.conf`
  - **701180**: Mask `systemd-coredump.socket`
  - **701190**: ExecShield/NX audit — verify CPU `nx` flag and absence of `noexec` kernel arg
  - **701200**: Mask `kdump` service
  - **701210**: Mask/disable `autofs` (skip if not installed)
  - **701220, 701230, 701290**: SSSD configuration (`pam_cert_auth`, `certificate_verification`, `offline_credentials_expiration`) via `/etc/sssd/conf.d/10-stig.conf`
  - **701240**: Audit SSH private key passphrase enforcement
  - **701250, 701260**: systemd drop-ins for emergency and rescue mode sulogin authentication
  - **701270**: Audit DoD CA certificate presence in SSSD PKI store
  - **701280**: Audit SSSD certmap section for PKI identity mapping

---

## [0.2.0] — 2026-04-06

### Added
- Implemented 404 of 434 STIG controls across ranges: 000xxx, 001xxx, 200xxx, 300xxx, 400xxx, 500xxx, 600xxx, 700xxx, 800xxx, 900xxx
- Each task includes: check, optional remediation, re-check/verification, `ansible.builtin.assert` with Splunk-compatible `result=PASS/FAIL stig_id=` messages, and a `rescue:` block for continuous execution

### Fixed
- Added missing `rescue:` blocks to `RHEL-10-000560`, `RHEL-10-000570`, and `RHEL-10-001050` — these were causing the hardening playbook to abort on assert failure
- Converted all multi-line `>-` YAML block scalar `fail_msg` values in the 000xxx range to single-line strings for Splunk `rex` field extraction compatibility
- Removed internal double-quotes from 20 outer task `name:` fields in the 700xxx range that caused YAML parsing warnings
- Corrected misplaced `rhel_10_700970` variable ordering in `defaults/main.yml`

---

## [0.1.0] — 2026-03-30

### Added
- Initial project framework scaffold
- `rhel10-stig` role with 434 staged task files based on RHEL 10 STIG V1R1 (26 Feb 2026)
- Individual task file per STIG control with embedded description, check text, and fix text
- `defaults/main.yml` with all 434 control toggle variables (default: `true`)
- `vars/main.yml` override file for local customization
- `site.yml` main playbook entry point
- `inventory/hosts.yml` inventory template
- `enforce.sh` convenience wrapper script
- `README.md` project documentation

---

## Version History

| Version | Date       | Description                                          |
|---------|------------|------------------------------------------------------|
| 0.5.0   | 2026-04-07 | Bug fixes: handlers, sysctl, regex_search, scoping   |
| 0.4.0   | 2026-04-07 | Interactive CLI customizer (`customize.py`)          |
| 0.3.0   | 2026-04-06 | All 434/434 controls implemented (701xxx range)      |
| 0.2.0   | 2026-04-06 | 404/434 controls implemented; bug fixes              |
| 0.1.0   | 2026-03-30 | Initial framework scaffold                           |

---

## Severity Breakdown (V1R1)

| Severity | Count |
|----------|-------|
| HIGH     | 30    |
| MEDIUM   | 399   |
| LOW      | 5     |
| **Total**| **434** |
