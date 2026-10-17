#!/usr/bin/env bash
# =============================================================================
# IBM® Business Automation Workflow Skills and Bob Modes — Installer
#
# Copyright 2026 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
#
# Requires: bash 3.2+ (macOS default), GNU/BSD coreutils
#
# USAGE
#   ./install.sh                        # install all skills (global scope)
#   ./install.sh --scope project        # install into .bob/skills/ in current dir
#   ./install.sh --skills "generate-baw-bpmn,create-baw-portal"
#   ./install.sh --dry-run              # preview what would be installed, no changes
#   ./install.sh --uninstall            # remove all installed skills and modes
#   ./install.sh --help
#
# WHAT IT DOES
#   1. Validates prerequisites (Python 3, required pip packages)
#   2. Copies selected skill leaf directories to ~/.bob/skills/<name>/
#      (or .bob/skills/<name>/ for --scope project)
#   3. Safely merges modes/*.yaml into both global modes files
#      (~/.bob/settings/custom_modes.yaml for Bob IDE and
#       ~/.bob/custom_modes.yaml for Bob Shell), or .bob/custom_modes.yaml
#      for --scope project, without overwriting any pre-existing custom modes
#   4. Creates .env (with placeholder values) if it does not already exist
#   5. Prints a summary of installed components and any warnings
# =============================================================================

set -euo pipefail

# ── Constants ─────────────────────────────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
# ENV_FILE is set after arg parsing (scope-dependent — project scope writes to PWD)
ENV_FILE="${SCRIPT_DIR}/.env"
# BOB_SKILLS_DIR and BOB_MODES_FILES are set after arg parsing (scope-dependent)
# BOB_MODES_FILE is the file currently being written by _install_modes
BOB_SKILLS_DIR="${HOME}/.bob/skills"
BOB_MODES_FILES=("${HOME}/.bob/settings/custom_modes.yaml" "${HOME}/.bob/custom_modes.yaml")
BOB_MODES_FILE=""

SKILLS_ROOT="${SCRIPT_DIR}/skills"
MODES_ROOT="${SCRIPT_DIR}/modes"
readonly SKILLS_ROOT MODES_ROOT

readonly VERSION="1.0.0"
readonly REPO_URL="https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes"

# ANSI colour codes (suppressed when stdout is not a tty)
if [ -t 1 ]; then
  C_BOLD="\033[1m"; C_RESET="\033[0m"; C_GREEN="\033[0;32m"
  C_YELLOW="\033[0;33m"; C_RED="\033[0;31m"; C_CYAN="\033[0;36m"
  C_DIM="\033[2m"
else
  C_BOLD=""; C_RESET=""; C_GREEN=""; C_YELLOW=""; C_RED=""; C_CYAN=""; C_DIM=""
fi

# ── State (bash 3.2 compatible — no associative arrays) ───────────────────────
# _SKILL_PATHS is a newline-separated list of "skill-name:category/skill-name"
_SKILL_PATHS=""
DRY_RUN=false
UNINSTALL=false
SCOPE="global"           # global | project
# Space-separated lists (no special chars in names so this is safe)
SELECTED_SKILLS=""
INSTALLED_SKILLS=""
INSTALLED_MODES=""
WARNINGS=""
WARN_COUNT=0

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${C_CYAN}[INFO]${C_RESET}  $*"; }
success() { echo -e "${C_GREEN}[OK]${C_RESET}    $*"; }
warn() {
  echo -e "${C_YELLOW}[WARN]${C_RESET}  $*"
  WARNINGS="${WARNINGS}${*}\n"
  WARN_COUNT=$((WARN_COUNT + 1))
}
error()   { echo -e "${C_RED}[ERROR]${C_RESET} $*" >&2; }
dim()     { echo -e "${C_DIM}$*${C_RESET}"; }

die() { error "$*"; exit 1; }

dry_notice() {
  $DRY_RUN && echo -e "${C_YELLOW}[DRY-RUN]${C_RESET} $*"
}

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
  printf '%b\n' \
    "" \
    "${C_BOLD}IBM® BAW Skills and Bob Modes Installer v${VERSION}${C_RESET}" \
    "${C_DIM}${REPO_URL}${C_RESET}" \
    "" \
    "${C_BOLD}USAGE${C_RESET}" \
    "  ./install.sh [OPTIONS]" \
    "" \
    "${C_BOLD}OPTIONS${C_RESET}" \
    "  --scope <global|project>  Install scope (default: global)" \
    "                            global  -> ~/.bob/skills/  (works in every project)" \
    "                            project -> .bob/skills/ in the current directory" \
    "  --skills <list>           Install specific skills only (comma-separated names)" \
    "                            e.g. \"generate-baw-bpmn,inspect-baw-processes\"" \
    "                            Omit to install all skills (recommended)" \
    "  --uninstall               Remove all BAW skills and modes from both locations" \
    "  --dry-run                 Preview changes without writing any files" \
    "  --help, -h                Show this help message" \
    "" \
    "${C_BOLD}EXAMPLES${C_RESET}" \
    "  ./install.sh                                 # Install everything globally (recommended)" \
    "  ./install.sh --scope project                 # Install into current project's .bob/" \
    "  ./install.sh --dry-run                       # Preview what would be installed" \
    "  ./install.sh --skills generate-baw-bpmn      # Install one specific skill" \
    "  ./install.sh --uninstall                     # Remove all BAW skills and modes" \
    "" \
    "${C_BOLD}AVAILABLE SKILLS${C_RESET}"
  _list_available_skills
  echo ""
}

# ── Discover available skills ─────────────────────────────────────────────────
# Populates _SKILL_PATHS with lines of "skill-name:category/skill-name"
# Layout: skills/<category>/<skill-name>/SKILL.md
_discover_skills() {
  _SKILL_PATHS=""
  if [ ! -d "${SKILLS_ROOT}" ]; then
    die "Skills directory not found: ${SKILLS_ROOT}"
  fi

  for category_dir in "${SKILLS_ROOT}"/*/; do
    [ -d "${category_dir}" ] || continue
    category_name="$(basename "${category_dir}")"
    for skill_dir in "${category_dir}"*/; do
      [ -d "${skill_dir}" ] || continue
      skill_name="$(basename "${skill_dir}")"
      if [ -f "${skill_dir}/SKILL.md" ]; then
        _SKILL_PATHS="${_SKILL_PATHS}${skill_name}:${category_name}/${skill_name}\n"
      fi
    done
  done
}

# Look up a skill's relative path by name; echoes empty string if not found
_skill_path() {
  local name="$1"
  echo -e "${_SKILL_PATHS}" | grep "^${name}:" | head -1 | cut -d: -f2-
}

# All skill names, sorted
_skill_names() {
  echo -e "${_SKILL_PATHS}" | grep -v '^$' | cut -d: -f1 | sort
}

_list_available_skills() {
  _discover_skills
  local prev_category=""
  while IFS= read -r line; do
    [ -z "${line}" ] && continue
    local name category
    name="$(echo "${line}" | cut -d: -f1)"
    category="$(echo "${line}" | cut -d: -f2- | cut -d/ -f1)"
    if [ "${category}" != "${prev_category}" ]; then
      echo -e "  ${C_BOLD}${category}${C_RESET}"
      prev_category="${category}"
    fi
    echo -e "    ${C_GREEN}•${C_RESET} ${name}"
  done < <(echo -e "${_SKILL_PATHS}" | grep -v '^$' | sort -t: -k2)
}

# ── Prerequisite checks ───────────────────────────────────────────────────────
_check_prerequisites() {
  info "Checking prerequisites…"

  # Python 3
  local python_cmd=""
  for cmd in python3 python; do
    if command -v "${cmd}" >/dev/null 2>&1; then
      if "${cmd}" --version 2>&1 | grep -q "Python 3"; then
        python_cmd="${cmd}"
        break
      fi
    fi
  done

  if [ -z "${python_cmd}" ]; then
    warn "Python 3 not found. Some skills require Python 3 to generate artifacts."
    warn "Install Python 3 from https://www.python.org/downloads/ and re-run this script."
  else
    local py_version
    py_version="$("${python_cmd}" --version 2>&1)"
    success "Python found: ${py_version}"

    # Check required pip packages
    local missing_packages=""
    for pkg_import in "yaml:pyyaml" "lxml:lxml"; do
      local import_name install_name
      import_name="$(echo "${pkg_import}" | cut -d: -f1)"
      install_name="$(echo "${pkg_import}" | cut -d: -f2)"
      if ! "${python_cmd}" -c "import ${import_name}" >/dev/null 2>&1; then
        missing_packages="${missing_packages} ${install_name}"
      fi
    done

    if [ -n "${missing_packages}" ]; then
      warn "Missing Python packages:${missing_packages}"
      warn "Install them with: ${python_cmd} -m pip install${missing_packages}"
    else
      success "Required Python packages present (pyyaml, lxml)"
    fi
  fi

  # Bob CLI
  if ! command -v bob >/dev/null 2>&1; then
    warn "IBM Bob CLI not found in PATH. Download Bob from https://bob.ibm.com"
    warn "Skills will still be installed; Bob must be present to use them."
  else
    local bob_ver
    bob_ver="$(bob --version 2>/dev/null || echo "version unknown")"
    success "IBM Bob CLI found: ${bob_ver}"
  fi

  echo ""
}

# ── Install a single skill ────────────────────────────────────────────────────
_install_skill() {
  local skill_name="$1"
  local rel_path
  rel_path="$(_skill_path "${skill_name}")"

  if [ -z "${rel_path}" ]; then
    warn "Unknown skill '${skill_name}' — skipping."
    return
  fi

  local src="${SKILLS_ROOT}/${rel_path}"
  local dest="${BOB_SKILLS_DIR}/${skill_name}"

  if [ ! -d "${src}" ]; then
    warn "Source directory not found for '${skill_name}': ${src} — skipping."
    return
  fi

  if $DRY_RUN; then
    dry_notice "Would copy ${src} → ${dest}"
    INSTALLED_SKILLS="${INSTALLED_SKILLS} ${skill_name}"
    return
  fi

  mkdir -p "${BOB_SKILLS_DIR}"
  rm -rf "${dest}"
  cp -r "${src}" "${dest}"
  success "Installed skill: ${skill_name} → ${dest}"
  INSTALLED_SKILLS="${INSTALLED_SKILLS} ${skill_name}"
}

# ── Merge modes ────────────────────────────────────────────────────────────────
_install_modes() {
  if [ ! -d "${MODES_ROOT}" ]; then
    warn "${MODES_ROOT}/ not found — skipping mode installation."
    return
  fi

  # Check if any yaml files exist
  local found=false
  for mf in "${MODES_ROOT}"/*.yaml; do
    [ -f "${mf}" ] && found=true && break
  done

  if ! $found; then
    info "No mode YAML files found in ${MODES_ROOT}/ — skipping."
    return
  fi

  for BOB_MODES_FILE in "${BOB_MODES_FILES[@]}"; do
    info "Merging Bob modes into ${BOB_MODES_FILE}…"

    for mode_file in "${MODES_ROOT}"/*.yaml; do
      [ -f "${mode_file}" ] || continue
      local mode_name
      mode_name="$(basename "${mode_file}" .yaml)"

      if $DRY_RUN; then
        # Extract slug so dry-run summary matches real install output
        local dry_slug
        dry_slug="$(grep -m1 'slug:' "${mode_file}" \
          | sed 's/.*slug:[[:space:]]*//' \
          | tr -d "\"'" | tr -d '[:space:]')"
        dry_slug="${dry_slug:-${mode_name}}"
        dry_notice "Would merge ${mode_name}.yaml into ${BOB_MODES_FILE}"
        _record_mode "${dry_slug}"
        continue
      fi

      _merge_mode_yaml "${mode_file}" "${mode_name}"
    done
  done
}

# Add a slug to INSTALLED_MODES once (modes are merged into several files)
_record_mode() {
  case " ${INSTALLED_MODES} " in
    *" $1 "*) ;;
    *) INSTALLED_MODES="${INSTALLED_MODES} $1" ;;
  esac
}

# Exact-match test: does <file> contain a top-level mode item whose `slug:` key
# equals <slug>? Only the item's own slug key counts (the key at the item's
# indent) — never text inside descriptions/instructions, never lookalike slugs
# such as "baw-admin-extra" for "baw-admin".
_slug_exists() {
  local file="$1" slug="$2"
  awk -v slug="${slug}" -v q="'" '
    function val(s) {
      sub(/^[ ]*(-[ ]+)?slug:[ ]*/, "", s); sub(/[ ]+#.*$/, "", s)
      gsub("[\"" q "]", "", s); gsub(/[ \t\r]/, "", s); return s
    }
    BEGIN { ind = -1; found = 0 }
    {
      match($0, /^[ ]*/); lead = RLENGTH
      isdash = ($0 ~ /^[ ]*-[ ]/)
      if (ind < 0 && isdash) ind = lead
      if (ind < 0) next
      if ((isdash && lead == ind && $0 ~ /^[ ]*-[ ]+slug:/) ||
          (!isdash && lead == ind + 2 && $0 ~ /^[ ]*slug:/)) {
        if (val($0) == slug) found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' "${file}" 2>/dev/null
}

_merge_mode_yaml() {
  local src_file="$1"
  local mode_label="$2"

  # Extract slug from source (pattern matches both "slug: val" and "- slug: val")
  local incoming_slug
  incoming_slug="$(grep -m1 'slug:' "${src_file}" \
    | sed 's/.*slug:[[:space:]]*//' \
    | tr -d "\"'" \
    | tr -d '[:space:]')"

  if [ -z "${incoming_slug}" ]; then
    warn "Could not determine slug for mode '${mode_label}' — skipping."
    return
  fi

  mkdir -p "$(dirname "${BOB_MODES_FILE}")"

  # Create target if missing
  if [ ! -f "${BOB_MODES_FILE}" ]; then
    echo "customModes: []" > "${BOB_MODES_FILE}"
    info "Created ${BOB_MODES_FILE}"
  fi

  # Check if slug already present (exact match on the mode's own slug key)
  if _slug_exists "${BOB_MODES_FILE}" "${incoming_slug}"; then
    info "Mode '${incoming_slug}' already present in custom_modes.yaml — skipping (not overwriting)."
    return
  fi

  # Normalise empty-list shorthand
  if grep -q 'customModes: \[\]' "${BOB_MODES_FILE}"; then
    local tmpfile
    tmpfile="$(mktemp)"
    sed 's/^customModes: \[\]$/customModes:/' "${BOB_MODES_FILE}" > "${tmpfile}"
    mv "${tmpfile}" "${BOB_MODES_FILE}"
  fi

  # Extract mode block (everything after the "customModes:" header line)
  local in_block=false
  local tmp_block
  tmp_block="$(mktemp)"
  while IFS= read -r line; do
    if echo "${line}" | grep -q '^customModes:'; then
      in_block=true
      continue
    fi
    $in_block && echo "${line}" >> "${tmp_block}"
  done < "${src_file}"

  if [ ! -s "${tmp_block}" ]; then
    warn "Mode file '${mode_label}' appears empty after customModes header — skipping."
    rm -f "${tmp_block}"
    return
  fi

  # Ensure the existing file ends with a newline so the first appended line
  # doesn't get glued onto the user's last line
  if [ -s "${BOB_MODES_FILE}" ] && [ -n "$(tail -c1 "${BOB_MODES_FILE}")" ]; then
    echo "" >> "${BOB_MODES_FILE}"
  fi
  cat "${tmp_block}" >> "${BOB_MODES_FILE}"
  rm -f "${tmp_block}"

  success "Merged mode: ${incoming_slug} → ${BOB_MODES_FILE}"
  _record_mode "${incoming_slug}"
}

# ── Create .env ───────────────────────────────────────────────────────────────
_create_env() {
  if [ -f "${ENV_FILE}" ]; then
    dim ".env already exists — not overwriting."
    return
  fi

  if $DRY_RUN; then
    dry_notice "Would create ${ENV_FILE}"
    return
  fi

  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  success "Created .env — open it and fill in your BAW server URL and credentials."
}

# ── Print summary ─────────────────────────────────────────────────────────────
_print_summary() {
  local dry_tag=""
  $DRY_RUN && dry_tag=" ${C_YELLOW}[DRY RUN — no files written]${C_RESET}"

  echo ""
  echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
  echo -e "${C_BOLD} Install Summary${C_RESET}${dry_tag}"
  echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"

  local skill_count=0
  local mode_count=0
  for s in ${INSTALLED_SKILLS}; do [ -n "${s}" ] && skill_count=$((skill_count + 1)); done
  for m in ${INSTALLED_MODES};  do [ -n "${m}" ] && mode_count=$((mode_count + 1));  done

  if [ "${skill_count}" -gt 0 ]; then
    echo -e "\n${C_GREEN}✔ Skills installed (${skill_count}):${C_RESET}"
    for s in ${INSTALLED_SKILLS}; do
      [ -n "${s}" ] && echo -e "  • ${s}"
    done
    echo -e "  ${C_DIM}Location: ${BOB_SKILLS_DIR}/${C_RESET}"
  else
    echo -e "\n${C_DIM}No skills installed.${C_RESET}"
  fi

  if [ "${mode_count}" -gt 0 ]; then
    echo -e "\n${C_GREEN}✔ Bob modes merged (${mode_count}):${C_RESET}"
    for m in ${INSTALLED_MODES}; do
      [ -n "${m}" ] && echo -e "  • ${m}"
    done
    for f in "${BOB_MODES_FILES[@]}"; do
      echo -e "  ${C_DIM}Location: ${f}${C_RESET}"
    done
  fi

  if [ "${WARN_COUNT}" -gt 0 ]; then
    echo -e "\n${C_YELLOW}⚠ Warnings (${WARN_COUNT}):${C_RESET}"
    echo -e "${WARNINGS}" | grep -v '^$' | while IFS= read -r w; do
      echo -e "  ${C_YELLOW}!${C_RESET} ${w}"
    done
  fi

  if [ "${skill_count}" -gt 0 ] && ! $DRY_RUN; then
    echo -e "\n${C_GREEN}${C_BOLD}✓ Setup complete!${C_RESET}"
    echo -e "  Open IBM Bob and switch to ${C_BOLD}IBM BAW Author${C_RESET} or ${C_BOLD}IBM BAW Admin${C_RESET} mode."
    echo -e "  Then try: ${C_CYAN}\"Generate a BAW BPMN process for expense approvals\"${C_RESET}"
    if [ -f "${ENV_FILE}" ]; then
      echo -e "\n  ${C_YELLOW}Next step:${C_RESET} Edit ${C_BOLD}.env${C_RESET} and replace the placeholder values with your BAW server URL and credentials."
    fi
  fi

  echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
  echo ""
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
_uninstall() {
  _discover_skills

  # Collect every known skill name from the repo
  local all_skills
  all_skills="$(_skill_names)"

  # Collect mode slugs from modes directory
  local mode_slugs=""
  if [ -d "${MODES_ROOT}" ]; then
    for mf in "${MODES_ROOT}"/*.yaml; do
      [ -f "${mf}" ] || continue
      local slug
      slug="$(grep -m1 'slug:' "${mf}" \
        | sed 's/.*slug:[[:space:]]*//' \
        | tr -d "\"'" | tr -d '[:space:]')"
      [ -n "${slug}" ] && mode_slugs="${mode_slugs} ${slug}"
    done
  fi

  # Locations to check (both global and project)
  local global_skills_dir="${HOME}/.bob/skills"
  local project_skills_dir="$(pwd)/.bob/skills"
  local global_modes_file="${HOME}/.bob/settings/custom_modes.yaml"
  local shell_modes_file="${HOME}/.bob/custom_modes.yaml"
  local project_modes_file="$(pwd)/.bob/custom_modes.yaml"

  local removed_count=0

  # Remove skill directories from both locations
  for location in "${global_skills_dir}" "${project_skills_dir}"; do
    for name in ${all_skills}; do
      [ -z "${name}" ] && continue
      local target="${location}/${name}"
      if [ -d "${target}" ]; then
        if $DRY_RUN; then
          dry_notice "Would remove ${target}"
        else
          rm -rf "${target}"
        fi
        removed_count=$((removed_count + 1))
      fi
    done
  done

  # Strip mode slugs from every custom_modes.yaml file
  for modes_file in "${global_modes_file}" "${shell_modes_file}" "${project_modes_file}"; do
    [ -f "${modes_file}" ] || continue
    for slug in ${mode_slugs}; do
      [ -z "${slug}" ] && continue
      if _slug_exists "${modes_file}" "${slug}"; then
        if $DRY_RUN; then
          dry_notice "Would remove mode '${slug}' from ${modes_file}"
        else
          _remove_mode_from_yaml "${modes_file}" "${slug}"
        fi
      fi
    done
  done

  if $DRY_RUN; then
    echo ""
    info "Dry run complete. No files were removed."
    return
  fi

  echo ""
  if [ "${removed_count}" -gt 0 ]; then
    echo -e "${C_GREEN}${C_BOLD}✓ IBM BAW skills and Bob modes have been successfully uninstalled.${C_RESET}"
  else
    echo -e "${C_YELLOW}Nothing to uninstall — no IBM BAW skills were found in ~/.bob/skills/ or .bob/skills/.${C_RESET}"
  fi
  echo ""
}

# Remove the whole list item whose own `slug:` key equals <slug>.
# The file is split into items at the list-item indent (taken from the first
# "- " line), so other modes — including ones with different key order,
# 4-space nested lists, or "slug:" text inside block scalars — are untouched.
_remove_mode_from_yaml() {
  local file="$1"
  local slug="$2"
  local tmp
  tmp="$(mktemp)"

  awk -v slug="${slug}" -v q="'" '
    function flush(   i) {
      if (n > 0 && !drop) for (i = 1; i <= n; i++) print buf[i]
      n = 0; drop = 0
    }
    function val(s) {
      sub(/^[ ]*(-[ ]+)?slug:[ ]*/, "", s); sub(/[ ]+#.*$/, "", s)
      gsub("[\"" q "]", "", s); gsub(/[ \t\r]/, "", s); return s
    }
    BEGIN { ind = -1; n = 0; drop = 0 }
    {
      match($0, /^[ ]*/); lead = RLENGTH
      isdash = ($0 ~ /^[ ]*-[ ]/)
      if (ind < 0 && isdash) ind = lead
      if (ind < 0) { print; next }
      if (isdash && lead == ind) flush()
      if ((isdash && lead == ind && $0 ~ /^[ ]*-[ ]+slug:/) ||
          (!isdash && lead == ind + 2 && $0 ~ /^[ ]*slug:/)) {
        if (val($0) == slug) drop = 1
      }
      n++; buf[n] = $0
    }
    END { flush() }
  ' "${file}" > "${tmp}"

  mv "${tmp}" "${file}"

  # Leave a valid empty list rather than a null "customModes:" key
  if ! grep -q 'slug:' "${file}"; then
    echo "customModes: []" > "${file}"
  fi
}

# ── Argument parsing ──────────────────────────────────────────────────────────
_parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --scope)
        [ -z "${2:-}" ] && die "--scope requires 'global' or 'project'."
        case "$2" in
          global|project) SCOPE="$2" ;;
          *) die "--scope must be 'global' or 'project', got: $2" ;;
        esac
        shift 2
        ;;
      --skills)
        [ -z "${2:-}" ] && die "--skills requires a comma-separated list of skill names."
        SELECTED_SKILLS="$(echo "$2" | tr ',' ' ')"
        shift 2
        ;;
      --uninstall)
        UNINSTALL=true
        shift
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown option: $1. Run ./install.sh --help for usage."
        ;;
    esac
  done
}

# ── Interactive prompt ────────────────────────────────────────────────────────
_prompt_selection() {
  local total=0
  for _s in $(_skill_names); do total=$((total + 1)); done

  local mode_count=0
  if [ -d "${MODES_ROOT}" ]; then
    for mf in "${MODES_ROOT}"/*.yaml; do
      [ -f "${mf}" ] && mode_count=$((mode_count + 1))
    done
  fi

  echo ""
  printf '%b' "  ${C_BOLD}${total} skills${C_RESET} and ${C_BOLD}${mode_count} Bob mode(s)${C_RESET} will be installed\n"
  echo ""
  printf '%b' "  Run ${C_CYAN}./install.sh --help${C_RESET} to see all available skills.\n"
  echo ""
  printf '%b' "Install all? ${C_BOLD}[Y/n]${C_RESET}: "
  read -r answer

  case "${answer}" in
    ""|[Yy]*)
      SELECTED_SKILLS="$(_skill_names | tr '\n' ' ')"
      ;;
    *)
      _picker_select
      ;;
  esac
}

# Numbered skill picker
_picker_select() {
  echo ""
  echo -e "${C_BOLD}Available skills:${C_RESET}"
  echo ""

  local idx=1
  local indexed_names=""

  while IFS= read -r name; do
    [ -z "${name}" ] && continue
    local rel category display
    rel="$(_skill_path "${name}")"
    if echo "${rel}" | grep -q '/'; then
      category="$(echo "${rel}" | cut -d/ -f1)"
      display="  ${C_DIM}${idx})${C_RESET}  ${name}  ${C_DIM}(${category})${C_RESET}"
    else
      display="  ${C_DIM}${idx})${C_RESET}  ${name}"
    fi
    printf '%b\n' "${display}"
    indexed_names="${indexed_names}${idx}:${name}\n"
    idx=$((idx + 1))
  done < <(_skill_names)

  local total=$((idx - 1))
  echo ""
  echo -e "  Enter numbers separated by spaces to select, or ${C_BOLD}all${C_RESET} to install everything:"
  printf '%b' "  > "
  read -r selection

  [ "${selection}" = "q" ] && { info "Aborted."; exit 0; }

  if [ "${selection}" = "all" ]; then
    SELECTED_SKILLS="$(_skill_names | tr '\n' ' ')"
    return
  fi

  for token in ${selection}; do
    if echo "${token}" | grep -qE '^[0-9]+$'; then
      if [ "${token}" -ge 1 ] && [ "${token}" -le "${total}" ]; then
        local matched
        matched="$(printf '%b' "${indexed_names}" | grep "^${token}:" | cut -d: -f2-)"
        SELECTED_SKILLS="${SELECTED_SKILLS} ${matched}"
      else
        warn "Index out of range: ${token} (valid: 1–${total})"
      fi
    else
      warn "Unrecognised selection: '${token}' — enter numbers or 'all'"
    fi
  done

  SELECTED_SKILLS="$(echo "${SELECTED_SKILLS}" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')"
  if [ -z "$(echo "${SELECTED_SKILLS}" | tr -d ' ')" ]; then
    die "No skills selected. Run ./install.sh --help for usage."
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  _parse_args "$@"

  # Resolve install locations based on scope
  if [ "${SCOPE}" = "project" ]; then
    BOB_SKILLS_DIR="$(pwd)/.bob/skills"
    BOB_MODES_FILES=("$(pwd)/.bob/custom_modes.yaml")
    ENV_FILE="$(pwd)/.env"
  fi

  echo ""
  echo -e "${C_BOLD}IBM® BAW Skills and Bob Modes Installer v${VERSION}${C_RESET}"
  dim "${REPO_URL}"
  echo ""

  # Uninstall path — no prereq check needed
  if $UNINSTALL; then
    _uninstall
    return
  fi

  _check_prerequisites
  _discover_skills

  if [ -z "$(echo -e "${_SKILL_PATHS}" | tr -d '[:space:]')" ]; then
    die "No skills found under ${SKILLS_ROOT}. Ensure you are running this script from the repository root."
  fi

  # If --skills was not given and we are in an interactive terminal, prompt the user.
  # In non-interactive environments (CI, pipes) default silently to all.
  if [ -z "$(echo "${SELECTED_SKILLS}" | tr -d ' ')" ]; then
    if [ -t 0 ]; then
      _prompt_selection
    else
      SELECTED_SKILLS="$(_skill_names | tr '\n' ' ')"
    fi
  fi

  # Validate and deduplicate
  local valid_skills=""
  for name in ${SELECTED_SKILLS}; do
    name="$(echo "${name}" | tr -d '[:space:]')"
    [ -z "${name}" ] && continue
    local rel
    rel="$(_skill_path "${name}")"
    if [ -n "${rel}" ]; then
      if ! echo "${valid_skills}" | grep -wq "${name}" 2>/dev/null; then
        valid_skills="${valid_skills} ${name}"
      fi
    else
      warn "Skill '${name}' not found in this repository — skipping."
    fi
  done

  valid_skills="$(echo "${valid_skills}" | tr ' ' '\n' | grep -v '^$' | tr '\n' ' ')"
  if [ -z "$(echo "${valid_skills}" | tr -d ' ')" ]; then
    die "No valid skills to install."
  fi

  local count=0
  for _s in ${valid_skills}; do count=$((count + 1)); done
  info "Installing ${count} skill(s)…"

  for skill in ${valid_skills}; do
    _install_skill "${skill}"
  done

  _install_modes
  _create_env
  _print_summary
}

main "$@"
