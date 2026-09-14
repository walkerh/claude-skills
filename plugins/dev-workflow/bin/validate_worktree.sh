#!/usr/bin/env bash
# validate_worktree.sh - Validates the Claude development environment.
#
# Checks:
#   1. Current git branch is "claude"
#   2. Worktree root directory is named "claude"
#   3. If .venv exists in the worktree root, it must be active

failures=0

worktree_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "FAIL: Not in a git repository"
    exit 1
fi

# Check 1: Current branch is "claude"
branch=$(git branch --show-current)
if [ "$branch" != "claude" ]; then
    echo "FAIL: Current branch is '$branch', expected 'claude'"
    failures=$((failures + 1))
fi

# Check 2: Worktree root directory is named "claude"
worktree_name=$(basename "$worktree_root")
if [ "$worktree_name" != "claude" ]; then
    echo "FAIL: Worktree directory is '$worktree_name', expected 'claude'"
    failures=$((failures + 1))
fi

# Check 3: If .venv exists, it must be active
venv_path="$worktree_root/.venv"
if [ -d "$venv_path" ]; then
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "FAIL: .venv exists but no virtual environment is active"
        failures=$((failures + 1))
    else
        resolved_venv=$(realpath "$venv_path")
        resolved_active=$(realpath "$VIRTUAL_ENV")
        if [ "$resolved_venv" != "$resolved_active" ]; then
            echo "FAIL: Active venv is '$VIRTUAL_ENV', expected '$venv_path'"
            failures=$((failures + 1))
        fi
    fi
fi

if [ "$failures" -eq 0 ]; then
    echo "OK: All checks passed"
fi

exit $failures
