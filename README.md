# Patch Automation Script

This repository contains a simple Python script to apply a git patch to a repository.
The script attempts a 3-way merge and, if conflicts occur, keeps the incoming
changes from the patch. The resulting changes are committed and pushed.

## Usage

```bash
python3 apply_patch.py --patch path/to/code.patch --repo /path/to/repo
```

Run the command from anywhere. The `--repo` option defaults to the current
working directory.

