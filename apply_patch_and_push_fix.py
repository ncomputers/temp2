import subprocess
import sys
from datetime import datetime

# Your full patch goes here (replace this with your actual patch)
INLINE_PATCH = r"""
<PASTE YOUR FULL PATCH CONTENT HERE — INCLUDING `diff --git` HEADERS>
"""

COMMIT_MESSAGE = f"Apply inline patch: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def run(cmd, input_text=None, ignore_error=False):
    result = subprocess.run(
        cmd,
        input=input_text,
        shell=isinstance(cmd, str),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0 and not ignore_error:
        print(f"[❌] Command failed: {cmd}\n{result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()

def apply_patch():
    print("[📥] Applying inline patch with 3-way merge...")
    out = run(["git", "apply", "--3way"], input_text=INLINE_PATCH, ignore_error=True)
    if out:
        print(out)

    # Check if patch applied by checking `git status`
    status = run("git status --porcelain")
    if not status:
        print("[ℹ️] No changes detected. Patch may not have applied.")
        sys.exit(0)
    else:
        print("[✅] Patch applied.")

def commit_and_push():
    print("[➕] Staging changes...")
    run("git add .")

    print("[📝] Committing...")
    commit_out = run(f'git commit -m "{COMMIT_MESSAGE}"', ignore_error=True)
    if "nothing to commit" in commit_out.lower():
        print("[ℹ️] Nothing to commit.")
        return

    print("[📤] Pushing to remote...")
    run("git push")
    print("[🚀] Done! Changes pushed.")

def main():
    apply_patch()
    commit_and_push()

if __name__ == "__main__":
    main()
