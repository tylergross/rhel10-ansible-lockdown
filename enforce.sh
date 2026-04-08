#!/usr/bin/env bash
# =============================================================================
# enforce.sh — rhel10-lockdown convenience wrapper
#
# Runs the RHEL 10 STIG hardening playbook against hosts defined in
# inventory/hosts.yml.  All arguments are passed directly to ansible-playbook.
#
# Usage:
#   ./enforce.sh                          Run all controls
#   ./enforce.sh --check                  Dry run (no changes applied)
#   ./enforce.sh --tags high              Run HIGH severity controls only
#   ./enforce.sh --tags high,medium       Run HIGH and MEDIUM controls
#   ./enforce.sh --tags RHEL-10-700970    Run a single STIG control
#   ./enforce.sh --skip-tags low          Skip LOW severity controls
#   ./enforce.sh --limit my-server        Target a single host
#   ./enforce.sh -e "rhel_10_700970=false" --check   Skip one control, dry run
#
# Requirements:
#   - ansible-playbook must be in PATH
#   - SSH access to target hosts configured in inventory/hosts.yml
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${SCRIPT_DIR}/inventory/hosts.yml"
PLAYBOOK="${SCRIPT_DIR}/site.yml"

# Verify ansible-playbook is available
if ! command -v ansible-playbook &>/dev/null; then
    echo "ERROR: ansible-playbook not found in PATH." >&2
    echo "Install Ansible: https://docs.ansible.com/ansible/latest/installation_guide/" >&2
    exit 1
fi

# Verify inventory exists
if [[ ! -f "${INVENTORY}" ]]; then
    echo "ERROR: Inventory file not found: ${INVENTORY}" >&2
    echo "Create and populate inventory/hosts.yml before running." >&2
    exit 1
fi

# Verify playbook exists
if [[ ! -f "${PLAYBOOK}" ]]; then
    echo "ERROR: Playbook not found: ${PLAYBOOK}" >&2
    exit 1
fi

echo "============================================================"
echo " rhel10-lockdown | RHEL 10 STIG V1R1 Enforcement"
echo "============================================================"
echo " Inventory : ${INVENTORY}"
echo " Playbook  : ${PLAYBOOK}"
echo " Arguments : $*"
echo "============================================================"
echo ""

# Run the playbook, forwarding all arguments
ansible-playbook \
    -i "${INVENTORY}" \
    "${PLAYBOOK}" \
    "$@"

echo ""
echo "============================================================"
echo " Playbook run complete."
echo "============================================================"
