# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.5.0] — 2026-04-07

### Added
- `benchmark/generate_rhel10_benchmark.py` — enhanced with real OVAL automated checks replacing `ind:unknown_test` stubs:
  - Pattern-based check-text categorization (15 categories) covering 294/434 rules (67%) with automated OVAL
  - `sysctl` (32) → `ind:textfilecontent54_test` on `/proc/sys/` paths
  - `grep` (89) + `pam` (13) + `sssd` (3) + `sshd_config` (18) → `ind:textfilecontent54_test` on target config files
  - `stat_owner` (17) + `stat_group` (17) → `unix:file_test` with `user_id`/`group_id` = 0
  - `stat_mode` (12) → `unix:file_test` with octal permission bit checks
  - `rpm_absent` (33) + `rpm_present` (2) → `linux:rpminfo_test` with `check_existence` flags
  - `systemctl_masked` (5) + `systemctl_enabled` (2) → `unix:file_test` on unit symlink paths
  - `cmdline` (6) + `proc_sys_cat` (1) → `ind:textfilecontent54_test` on `/proc/cmdline`
  - `modprobe` (5) + `audit` (38) → `ind:textfilecontent54_test` on glob paths
  - Remaining 140 rules use `ind:unknown_test` (manual review required)
- `benchmark/U_RHEL_10_V1R1_STIG_SCAP_1-3_Benchmark.xml` — regenerated (2.6 MB) with automated OVAL checks; XML validated well-formed

---

## [0.4.0] — 2026-04-07

### Added
- `benchmark/generate_rhel10_benchmark.py` — Python script that parses all 434 Ansible task file headers and generates a SCAP 1.3 data stream XML benchmark
- `benchmark/U_RHEL_10_V1R1_STIG_SCAP_1-3_Benchmark.xml` — generated SCAP 1.3 benchmark (2.5 MB) mirroring the RHEL 9 V2R8 structure:
  - XCCDF benchmark with all 434 rules, including title, description, check text, fix text, CCI ident, and fix references
  - 11 profiles (MAC-1/2/3 × Classified/Public/Sensitive + Disable_Slow_Rules + CAT_I_Only)
  - OVAL stubs using `ind:unknown_test` — all rules correctly report "not evaluated", suitable for STIG Viewer manual tracking
  - CPE dictionary and platform OVAL for `cpe:/o:redhat:enterprise_linux:10`

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
| 0.5.0   | 2026-04-07 | Real OVAL automated checks (294/434, 67% coverage)   |
| 0.4.0   | 2026-04-07 | SCAP 1.3 benchmark generated from task files         |
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
