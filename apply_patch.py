#!/usr/bin/env python3
"""Apply a patch to a Git repository with automatic conflict resolution.

This script uses `git apply --3way` to merge the given patch. If conflicts
occur, the conflict regions are resolved by keeping the incoming lines from
the patch. Finally, the script commits and pushes the changes.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime


def run(cmd, cwd=None, input_text=None, ignore_error=False):
    """Run a command and return its stdout."""
    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        text=True,
        input=input_text,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0 and not ignore_error:
        print(f"[❌] Command failed: {cmd}\n{result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def validate_paths(patch_path, repo_path):
    """Ensure the patch file and repo path exist and look valid."""
    if not os.path.isfile(patch_path):
        print(f"[❌] Patch file not found: {patch_path}")
        sys.exit(1)
    if not os.path.isdir(repo_path):
        print(f"[❌] Repo path not found: {repo_path}")
        sys.exit(1)
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"[❌] Not a Git repository: {repo_path}")
        sys.exit(1)


def parse_patch_files(patch_path):
    """Return a list of files modified by the patch."""
    with open(patch_path, "r", encoding="utf-8") as f:
        text = f.read()
    return re.findall(r"^\+\+\+ b/(.+)", text, flags=re.MULTILINE)


def has_conflict_markers(path):
    """Check whether a file contains git conflict markers."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("<<<<<<<"):
                return True
    return False


def resolve_conflicts(path):
    """Replace conflict regions by taking the incoming changes."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    resolved = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            i += 1
            while i < len(lines) and not lines[i].startswith("======="):
                i += 1
            i += 1  # Skip the separator
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                resolved.append(lines[i])
                i += 1
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                i += 1
            i += 1
        else:
            resolved.append(lines[i])
            i += 1

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(resolved)


def apply_patch(patch_path, repo_path):
    """Apply the patch using git and resolve conflicts."""
    print("[📥] Applying patch with 3-way merge...")
    try:
        run(["git", "apply", "--3way", patch_path], cwd=repo_path)
    except SystemExit:
        print("[⚠️] Patch failed. Attempting --reject fallback...")
        run(["git", "apply", "--reject", patch_path], cwd=repo_path)

    files = parse_patch_files(patch_path)
    for fpath in files:
        abs_path = os.path.join(repo_path, fpath)
        if os.path.exists(abs_path) and has_conflict_markers(abs_path):
            resolve_conflicts(abs_path)
            run(["git", "add", fpath], cwd=repo_path)


def commit_and_push(repo_path):
    """Commit staged changes and push to the remote."""
    print("[➕] Staging changes...")
    run("git add .", cwd=repo_path)

    print("[📝] Committing...")
    commit_msg = f"Auto-patch: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    out = run(["git", "commit", "-m", commit_msg], cwd=repo_path, ignore_error=True)

    if "nothing to commit" in out.lower():
        print("[ℹ️] Nothing new to commit.")
        return

    print("[📤] Pushing to remote...")
    run("git push", cwd=repo_path)
    print("[🚀] Patch applied, committed, and pushed!")


def main():
    parser = argparse.ArgumentParser(description="Apply a Git patch to a repository.")
    parser.add_argument("--patch", required=True, help="Path to .patch file")
    parser.add_argument("--repo", default=".", help="Path to Git repository")
    args = parser.parse_args()

    patch_path = os.path.abspath(args.patch)
    repo_path = os.path.abspath(args.repo)

    validate_paths(patch_path, repo_path)
    apply_patch(patch_path, repo_path)
    commit_and_push(repo_path)


if __name__ == "__main__":
    main()
