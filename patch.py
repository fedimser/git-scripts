#!/usr/bin/env python3
# Copies changes from one branch to another.
import subprocess
import sys
import os

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 patch.py branch1 branch2")
        sys.exit(1)

    branch1, branch2 = sys.argv[1], sys.argv[2]

    for branch in [branch1, branch2]:
        result = run(f"git rev-parse --verify {branch}")
        if result.returncode != 0:
            print(f"Branch '{branch}' does not exist")
            sys.exit(1)

    result = run(f"git checkout {branch1}")
    if result.returncode != 0:
        print(f"Failed to checkout {branch1}")
        sys.exit(1)

    result = run("git --no-pager diff --name-only origin/master...HEAD")
    if result.returncode != 0:
        print("Failed to get changed files")
        sys.exit(1)

    files = [f for f in result.stdout.strip().split('\n') if f]
    print("Changed files:")
    for f in files:
        print(f"  {f}")
    
    confirm = input("Proceed? [y/N]: ")
    if confirm.lower() != 'y':
        print("Aborted")
        sys.exit(0)

    file_contents = {}
    for f in files:
        with open(f, 'r') as fp:
            file_contents[f] = fp.read()

    result = run(f"git checkout {branch2}")
    if result.returncode != 0:
        print(f"Failed to checkout {branch2}")
        sys.exit(1)

    for f, content in file_contents.items():
        os.makedirs(os.path.dirname(f) or '.', exist_ok=True)
        with open(f, 'w') as fp:
            fp.write(content)

    print(f"Patched {len(files)} files")

if __name__ == "__main__":
    main()
