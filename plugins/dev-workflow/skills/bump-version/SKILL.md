---
name: bump-version
description: Bump the version in pyproject.toml, commit, and create an annotated release tag
---

# Bump Version

Bump the project version, commit the change, and create an annotated git tag.

## Purpose

The primary job of this skill is to compose a meaningful annotated tag message,
then hand off the mechanical steps to the `bump-version` script. The value is
in the AI-composed release notes; the script handles file editing, committing,
and tagging. Fail immediately if the script exits non-zero.

## Steps

1. Determine the target version from the invocation args (e.g., `/bump-version 1.2.0`).

2. Gather context:
   - Read `pyproject.toml` to confirm the current version.
   - Run `git tag --sort=-version:refname` to find the most recent tag.
   - Run `git log <last-tag>..HEAD --oneline` (or all commits if no tags exist)
     to see what has changed since the last release.

3. Compose the annotated tag message:
   - If the user has provided bullet points or key points, use them as the
     basis for the message.
   - Otherwise, derive the message from recent commits and ask the user to
     confirm or amend before proceeding.
   - Keep the tone factual and concise — no marketing language.

4. Pipe the message to the script via stdin using a Bash heredoc:
   ```bash
   bump-version VERSION <<'EOF'
   <composed message>
   EOF
   ```
   Stop immediately if the script exits non-zero and surface the error to the user.

   `bump-version` ships in this plugin's `bin/`, which is added to `PATH` when
   the plugin is enabled. If it is not found, invoke it explicitly as
   `"${CLAUDE_PLUGIN_ROOT}/bin/bump-version"`.

5. Confirm success by running `git show vVERSION --stat`.
