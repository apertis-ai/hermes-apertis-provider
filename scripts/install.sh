#!/bin/sh

set -eu

repository=${APERTIS_PLUGIN_REPOSITORY:-https://github.com/apertis-ai/hermes-apertis-provider.git}
plugin_ref=${APERTIS_PLUGIN_REF:-}
hermes_home=${HERMES_HOME:-"$HOME/.hermes"}
target=$hermes_home/plugins/model-providers/apertis
parent=$hermes_home/plugins/model-providers
temporary=
temporary_name=
install_lock=$parent/.apertis-install.flock
fetch_checkout=
fetch_ref=
fetch_token_directory=

fail() {
    printf '%s\n' "Apertis provider install failed: $*" >&2
    exit 1
}

cleanup() {
    if [ -n "$temporary" ] && [ -d "$temporary" ]; then
        rm -rf "$temporary"
    fi
    if [ -n "$fetch_ref" ] && [ -n "$fetch_checkout" ]; then
        git -C "$fetch_checkout" update-ref -d "$fetch_ref" 2>/dev/null || :
    fi
    if [ -n "$fetch_token_directory" ] && [ -d "$fetch_token_directory" ]; then
        rmdir "$fetch_token_directory" 2>/dev/null || :
    fi
}

canonicalize_selected_ref() {
    candidate_ref=$1
    case "$candidate_ref" in
        refs/heads/*|refs/tags/*) printf '%s\n' "$candidate_ref" ;;
        v[0-9]*) printf 'refs/tags/%s\n' "$candidate_ref" ;;
        *) printf 'refs/heads/%s\n' "$candidate_ref" ;;
    esac
}

resolve_remote_default_ref() {
    checkout=$1
    remote_head=$(git -C "$checkout" ls-remote --symref origin HEAD) || \
        fail "could not resolve the origin default branch"
    case "$remote_head" in
        "ref: refs/heads/"*)
            default_ref=${remote_head#ref: }
            default_ref=${default_ref%%[[:space:]]HEAD*}
            case "$default_ref" in
                refs/heads/*) printf '%s\n' "$default_ref" ;;
                *) fail "origin HEAD did not resolve to a branch" ;;
            esac
            ;;
        *) fail "origin HEAD did not resolve to a branch" ;;
    esac
}

fetch_selected_commit() {
    fetch_checkout=$1
    remote_ref=$2
    fetch_token_directory=$(mktemp -d "$parent/.apertis-fetch-token.XXXXXX") || \
        fail "could not allocate a private fetch ref"
    fetch_token=${fetch_token_directory##*.}
    rmdir "$fetch_token_directory" || fail "could not release fetch token directory"
    fetch_token_directory=
    fetch_ref=refs/hermes-apertis-installer/$fetch_token

    git -C "$fetch_checkout" fetch --quiet --no-tags --no-write-fetch-head \
        origin "$remote_ref:$fetch_ref" || fail "could not fetch ref $remote_ref"
    fetched_commit=$(git -C "$fetch_checkout" rev-parse --verify \
        "${fetch_ref}^{commit}") || fail "could not resolve ref $remote_ref"
    git -C "$fetch_checkout" update-ref -d "$fetch_ref" || \
        fail "could not remove private fetch ref"
    fetch_ref=
    fetch_checkout=
}

normalize_repository() {
    normalized=$1
    normalized=${normalized%/}
    normalized=${normalized%.git}
    printf '%s\n' "$normalized"
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v mktemp >/dev/null 2>&1 || fail "mktemp is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"

mkdir -p "$parent"
if [ "${APERTIS_INSTALL_LOCK_HELD:-}" != "$install_lock" ]; then
    exec python3 -c '
import fcntl
import os
import subprocess
import sys

lock_path, script_path, *script_args = sys.argv[1:]
try:
    lock_handle = open(lock_path, "a+", encoding="utf-8")
except OSError as exc:
    print(f"Apertis provider install failed: could not open install lock: {exc}", file=sys.stderr)
    raise SystemExit(1)

with lock_handle:
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Apertis provider install failed: another install or update is running", file=sys.stderr)
        raise SystemExit(1)

    child_environment = os.environ.copy()
    child_environment["APERTIS_INSTALL_LOCK_HELD"] = lock_path
    try:
        completed = subprocess.run(
            ["sh", script_path, *script_args],
            env=child_environment,
            check=False,
        )
    except KeyboardInterrupt:
        raise SystemExit(130)
    raise SystemExit(completed.returncode)
' "$install_lock" "$0" "$@"
fi

trap cleanup 0
trap 'exit 1' HUP INT TERM

if [ -e "$target" ] || [ -L "$target" ]; then
    inside_work_tree=$(git -C "$target" rev-parse --is-inside-work-tree 2>/dev/null) || \
        fail "$target exists but is not a Git checkout"
    [ "$inside_work_tree" = "true" ] || fail "$target is not a Git work tree"
    checkout_root=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || \
        fail "could not resolve the Git checkout root for $target"
    checkout_root=$(cd "$checkout_root" 2>/dev/null && pwd -P) || \
        fail "could not canonicalize the Git checkout root for $target"
    target_root=$(cd "$target" 2>/dev/null && pwd -P) || \
        fail "could not canonicalize $target"
    [ "$target_root" = "$checkout_root" ] || \
        fail "$target is inside a Git checkout but is not its root"

    actual_repository=$(git -C "$target" config --get-all remote.origin.url 2>/dev/null) || \
        fail "$target has no origin remote"
    case "$actual_repository" in
        *'
'*) fail "$target origin has multiple fetch URLs" ;;
    esac
    expected_repository=$(normalize_repository "$repository")
    actual_repository=$(normalize_repository "$actual_repository")
    [ "$actual_repository" = "$expected_repository" ] || \
        fail "$target origin does not match $repository"

    checkout_status=$(git -C "$target" status --porcelain --untracked-files=all) || \
        fail "could not inspect $target for local changes"
    [ -z "$checkout_status" ] || \
        fail "$target has local changes; commit or remove them before updating"

    if [ -z "$plugin_ref" ]; then
        remote_ref=$(resolve_remote_default_ref "$target")
        selected_ref=${remote_ref#refs/heads/}
    else
        selected_ref=$plugin_ref
        remote_ref=$(canonicalize_selected_ref "$selected_ref")
    fi

    fetch_selected_commit "$target" "$remote_ref"
    target_commit=$fetched_commit
    git -C "$target" merge-base --is-ancestor HEAD "$target_commit" || \
        fail "ref $selected_ref is not a fast-forward from the installed revision"

    added_paths=$(git -C "$target" -c core.quotePath=false diff --name-only \
        --no-renames --diff-filter=A HEAD "$target_commit") || \
        fail "could not inspect paths added by ref $selected_ref"
    previous_ifs=$IFS
    IFS='
'
    set -f
    for relative_path in $added_paths; do
        case "$relative_path" in
            \"*)
                set +f
                IFS=$previous_ifs
                fail "ref $selected_ref adds a path that cannot be inspected safely"
                ;;
        esac
        ancestor_path=$relative_path
        while [ "${ancestor_path#*/}" != "$ancestor_path" ]; do
            ancestor_path=${ancestor_path%/*}
            if [ -L "$target/$ancestor_path" ] || \
                { [ -e "$target/$ancestor_path" ] && \
                    [ ! -d "$target/$ancestor_path" ]; }; then
                if ! git -C "$target" ls-files --error-unmatch -- \
                    "$ancestor_path" >/dev/null 2>&1; then
                    set +f
                    IFS=$previous_ifs
                    fail "ref $selected_ref would replace local ancestor $ancestor_path"
                fi
            fi
        done
        if [ -e "$target/$relative_path" ] || [ -L "$target/$relative_path" ]; then
            tracked_paths=$(git -C "$target" ls-files -- "$relative_path") || {
                set +f
                IFS=$previous_ifs
                fail "could not inspect tracked paths under $relative_path"
            }
            ignored_paths=$(git -C "$target" ls-files --others --ignored \
                --exclude-standard -- "$relative_path") || {
                set +f
                IFS=$previous_ifs
                fail "could not inspect ignored paths under $relative_path"
            }
            if [ ! -d "$target/$relative_path" ] || \
                [ -L "$target/$relative_path" ] || \
                [ -z "$tracked_paths" ] || [ -n "$ignored_paths" ]; then
                set +f
                IFS=$previous_ifs
                fail "ref $selected_ref would overwrite local path $relative_path"
            fi
        fi
    done
    set +f
    IFS=$previous_ifs

    git -C "$target" merge --quiet --ff-only "$target_commit" || \
        fail "could not fast-forward to ref $selected_ref"

    trap - 0 HUP INT TERM
    printf '%s\n' "Updated Apertis provider at $target to $selected_ref"
    exit 0
fi

[ ! -e "$target" ] && [ ! -L "$target" ] || \
    fail "$target appeared while preparing the installation"
temporary=$(mktemp -d "$parent/.apertis-install.XXXXXX") || \
    fail "could not create a temporary install directory"
temporary_name=${temporary##*/}

if [ -n "$plugin_ref" ]; then
    git clone --quiet --no-checkout "$repository" "$temporary" || \
        fail "could not clone repository"
    remote_ref=$(canonicalize_selected_ref "$plugin_ref")
    fetch_selected_commit "$temporary" "$remote_ref"
    git -C "$temporary" checkout --quiet --detach "$fetched_commit" || \
        fail "could not check out ref $plugin_ref"
else
    git clone --quiet "$repository" "$temporary" || fail "could not clone repository"
fi

[ ! -e "$target" ] && [ ! -L "$target" ] || \
    fail "$target appeared while cloning the provider"
mv "$temporary" "$target" || fail "could not publish the provider checkout"
if [ -d "$target/$temporary_name" ]; then
    temporary=$target/$temporary_name
    fail "$target appeared while publishing the provider"
fi
[ ! -e "$temporary" ] && [ ! -L "$temporary" ] || \
    fail "temporary provider checkout was not published"
temporary=
trap - 0 HUP INT TERM
printf '%s\n' "Installed Apertis provider at $target"
