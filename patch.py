#!/usr/bin/env python3
# Copies changes from one branch to another.
# Source branch (branch1) is read via git show/diff only, so it can be checked out in another 
# worktree.
# 
# Usage: python3 patch.py branch1 branch2
import subprocess
import sys
import os

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def get_worktree_for_branch(branch) -> str | None:
    """Return the worktree path if branch is checked out in any worktree, else None."""
    result = run("git worktree list --porcelain")
    if result.returncode != 0:
        return None
    current_path: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = line.split(" ", 1)[1].strip()
        elif line.startswith("branch ") and current_path is not None:
            ref = line.split(" ", 1)[1].strip()  # refs/heads/branch-name
            if ref == f"refs/heads/{branch}":
                return current_path
            current_path = None
    return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 patch.py branch1 branch2")
        sys.exit(1)

    branch1, branch2 = sys.argv[1], sys.argv[2]

    for branch in [branch1, branch2]:
        result = run(f"git rev-parse --verify {branch}")
        if result.returncode != 0:
            print(f"Branch '{branch}' does not exist: {result.stderr.strip()}")
            sys.exit(1)

    # Get changed files from branch1 without checking it out.
    result = run(f"git --no-pager diff --name-only origin/main...{branch1}")
    if result.returncode != 0:
        print(f"Failed to get changed files: {result.stderr.strip()}")
        sys.exit(1)

    files = [f for f in result.stdout.strip().split("\n") if f]
    print("Changed files:")
    for f in files:
        print(f"  {f}")

    confirm = input("Proceed? [y/N]: ")
    if confirm.lower() != "y":
        print("Aborted")
        sys.exit(0)

    # Get file contents from branch1 without checking it out.
    file_contents = {}
    for f in files:
        result = run(f"git show {branch1}:{f}")
        if result.returncode != 0:
            print(f"Failed to read {f} from {branch1}: {result.stderr.strip()}")
            sys.exit(1)
        file_contents[f] = result.stdout

    branch2_worktree = get_worktree_for_branch(branch2)
    if branch2_worktree is not None:
        # branch2 is checked out in another worktree — apply patch there
        target_dir = branch2_worktree
        print(f"Applying patch in branch2 worktree: {target_dir}")
    else:
        result = run(f"git checkout {branch2}")
        if result.returncode != 0:
            print(f"Failed to checkout {branch2}: {result.stderr.strip()}")
            sys.exit(1)
        target_dir = "."

    for f, content in file_contents.items():
        dest_dir = os.path.join(target_dir, os.path.dirname(f)) if os.path.dirname(f) else target_dir
        os.makedirs(dest_dir or ".", exist_ok=True)
        dest_file = os.path.join(target_dir, f)
        with open(dest_file, "w") as fp:
            fp.write(content)

    print(f"Patched {len(files)} files")

if __name__ == "__main__":
    main()
