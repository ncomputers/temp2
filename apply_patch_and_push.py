import subprocess
import sys
import os
from datetime import datetime

PATCH_FILE = "code.patch"
COMMIT_MESSAGE = f"Auto-patch: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def run(cmd, ignore_error=False):
    result = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = result.stdout.strip() + "\n" + result.stderr.strip()
    if result.returncode != 0 and not ignore_error:
        print(f"[❌] Command failed: {cmd}\n{out}")
        sys.exit(1)
    return out.strip()

def main():
    print("[📦] Generating patch...")
    run(f"git diff --full-index --binary > {PATCH_FILE}", ignore_error=True)

    if os.path.getsize(PATCH_FILE) == 0:
        print("[ℹ️] No changes to patch. Skipping apply.")
        sys.exit(0)

    print("[➕] Staging changes...")
    run("git add .")

    print("[📝] Committing...")
    out = run(f'git commit -m "{COMMIT_MESSAGE}"', ignore_error=True)

    if "nothing to commit" in out.lower():
        print("[ℹ️] Nothing new to commit.")
        sys.exit(0)
    else:
        print("[✅] Commit complete.")

    print("[📤] Pushing...")
    run("git push")
    print("[🚀] Done! Patch created, committed, and pushed.")

if __name__ == "__main__":
    main()
