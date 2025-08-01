#!/usr/bin/env python3
"""Apply a patch file to the current git repo.

This script attempts to apply the patch using a 3-way merge. If conflicts
occur, it resolves them automatically by preferring the new lines from the
patch. Finally it commits and pushes the changes.
"""
import subprocess
import sys
import re
import os


def run(cmd):
    """Run a shell command and print its output."""
    result = subprocess.run(cmd, shell=True, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def parse_patch_files(patch_path):
    """Return a list of files modified by the patch."""
    with open(patch_path, "r", encoding="utf-8") as f:
        text = f.read()
    return re.findall(r'^\+\+\+ b/(.+)', text, flags=re.MULTILINE)


def has_conflict_markers(path):
    """Check if a file contains git conflict markers."""
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
            # Skip current version lines
            i += 1
            while i < len(lines) and not lines[i].startswith("======="):
                i += 1
            # Skip the separator
            i += 1
            # Keep incoming version
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                resolved.append(lines[i])
                i += 1
            # Skip end marker
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                i += 1
            i += 1
        else:
            resolved.append(lines[i])
            i += 1

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(resolved)


def main():
    patch = sys.argv[1] if len(sys.argv) > 1 else "code.patch"
    files = parse_patch_files(patch)

    # Try applying with a 3-way merge
    run(f"git apply -3 {patch}")

    # Resolve any conflicts by preferring the patch version
    for fpath in files:
        if os.path.exists(fpath) and has_conflict_markers(fpath):
            resolve_conflicts(fpath)
            run(f"git add {fpath}")

    # Add and commit all modified files
    run("git add -A")
    run(f"git commit -m 'Apply patch {patch}'")
    run("git push")


if __name__ == "__main__":
    main()
