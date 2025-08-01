import os
import subprocess
import shutil
from pathlib import Path
import argparse
import sys

log_entries = []

def log(msg):
    print(msg)
    log_entries.append(msg)

def write_log_file(log_path):
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_entries))

def run_cmd(cmd, cwd=None, show=True, dry_run=False):
    if show:
        log(f"[🔧] Running: {' '.join(cmd)}")
    if dry_run:
        log("[🟡] Dry run: command not executed.")
        return True, ""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log(f"[❌] Command failed: {' '.join(cmd)}")
        log(e.stderr.strip())
        return False, e.stderr.strip()

def has_conflicts(repo):
    conflict_files = []
    for root, _, files in os.walk(repo):
        for file in files:
            path = Path(root) / file
            if file.endswith('.rej') or file.endswith('.orig'):
                conflict_files.append(path)
            else:
                try:
                    with open(path, 'r', errors='ignore') as f:
                        if '<<<<<<<' in f.read():
                            conflict_files.append(path)
                except:
                    continue
    return conflict_files

def backup_and_resolve(repo, conflict_files, dry_run=False):
    resolved = []
    for file in conflict_files:
        try:
            if not file.exists():
                continue
            backup_file = file.with_suffix(file.suffix + ".bak")
            if not dry_run:
                shutil.copy(file, backup_file)

            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            new_lines = []
            in_conflict = False
            keep_new = False

            for line in lines:
                if line.startswith("<<<<<<<"):
                    in_conflict = True
                    keep_new = False
                    continue
                elif line.startswith("=======") and in_conflict:
                    keep_new = True
                    continue
                elif line.startswith(">>>>>>>") and in_conflict:
                    in_conflict = False
                    continue
                elif not in_conflict or keep_new:
                    new_lines.append(line)

            if not dry_run:
                with open(file, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

            resolved.append(str(file.relative_to(repo)))
            log(f"[🔧] Resolved conflicts in: {file.name} (backup saved)")
        except Exception as e:
            log(f"[⚠️] Failed to resolve {file}: {e}")
    return resolved

def apply_patch(repo, patch_path, dry_run=False):
    log("[📥] Applying patch with 3-way merge...")
    success, _ = run_cmd(['git', 'apply', '--3way', str(patch_path)], cwd=repo, dry_run=dry_run)
    if success:
        log("[✅] Patch applied cleanly.")
        return True
    log("[⚠️] Patch had conflicts or failed.")
    return False

def fallback_attempt(repo, patch_path, dry_run=False):
    log("[🔁] Attempting fallback...")
    run_cmd(['git', 'reset', '--hard'], cwd=repo, dry_run=dry_run)
    run_cmd(['git', 'clean', '-fd'], cwd=repo, dry_run=dry_run)
    return apply_patch(repo, patch_path, dry_run=dry_run)

def auto_commit_and_push(repo, commit_msg, push, dry_run=False):
    log("[💾] Committing changes...")

    patch_file = Path(sys.argv[0]).with_name("code.patch").name
    script_file = Path(sys.argv[0]).name
    log_file = "patch_apply.log"

    # Add everything
    run_cmd(['git', 'add', '--all'], cwd=repo, dry_run=dry_run)

    # Exclude this script, patch file, and log file from the commit
    run_cmd(['git', 'reset', patch_file, script_file, log_file], cwd=repo, dry_run=dry_run)

    # Commit
    run_cmd(['git', 'commit', '-m', commit_msg], cwd=repo, dry_run=dry_run)

    if push:
        log("[⬆️] Pushing to remote...")
        run_cmd(['git', 'push'], cwd=repo, dry_run=dry_run)

def main():
    parser = argparse.ArgumentParser(description="Auto-resolve patch applier")
    parser.add_argument("--patch", required=False, help="Path to .patch file (default: code.patch in script dir)")
    parser.add_argument("--repo", required=False, help="Path to Git repository (default: current working dir)")
    parser.add_argument("--auto-commit", action="store_true", help="Auto commit after applying patch")
    parser.add_argument("--auto-push", action="store_true", help="Push to remote after commit")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making changes")

    args = parser.parse_args()

    # Default paths
    script_dir = Path(__file__).resolve().parent
    patch_path = Path(args.patch) if args.patch else script_dir / "code.patch"
    repo_path = Path(args.repo) if args.repo else Path.cwd()

    if not patch_path.is_file():
        log(f"[❌] Patch file not found: {patch_path}")
        return
    if not (repo_path / '.git').exists():
        log(f"[❌] Not a valid Git repository: {repo_path}")
        return

    log(f"[🛠️] Starting patch apply: {patch_path.name} into {repo_path}")
    success = apply_patch(repo_path, patch_path, dry_run=args.dry_run)

    if not success:
        success = fallback_attempt(repo_path, patch_path, dry_run=args.dry_run)

    conflicts = has_conflicts(repo_path)
    if conflicts:
        resolved = backup_and_resolve(repo_path, conflicts, dry_run=args.dry_run)
        if resolved:
            log("[✅] Conflicts resolved by keeping patched version.")
            auto_commit_and_push(
                repo_path,
                "Applied patch with auto-resolve",
                push=args.auto_push,
                dry_run=args.dry_run
            )
        else:
            log("[❌] Some conflicts could not be resolved. Manual review needed.")
    elif success:
        log("[✅] Patch applied cleanly.")
        auto_commit_and_push(
            repo_path,
            "Applied patch cleanly",
            push=args.auto_push,
            dry_run=args.dry_run
        )

    log_path = Path.cwd() / "patch_apply.log"
    write_log_file(log_path)
    log(f"[📝] Log saved to: {log_path}")

if __name__ == "__main__":
    main()
