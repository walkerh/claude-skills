---
name: release-pr
description: Create a PR for the current branch and save merge commit message
---

# Release PR

Create a pull request for the current branch and prepare the merge commit message.

## Purpose

The primary job of this skill is to generate the PR title, PR body, and merge commit message based on the branch changes. The human will review and correct these items as needed. The mechanical steps (push, create PR, open browser) could be scripted; the value is in the AI-generated content.

This skill assumes a specific set of git conventions — a standing local-only
`claude` branch, a gitignored `local/` directory, and a `PR #{id} {branch}`
merge title format. See the plugin README if any of those are unfamiliar.

## Steps

0. Check the current branch (`git branch --show-current`). If it is `claude`
   (the standing work branch), rename before proceeding:
   - Run `git log main..HEAD --oneline` to review the commits ahead of main.
   - Propose a descriptive kebab-case branch name for the change (matching
     the convention used below, e.g. `fix-some-bug`).
   - Get an explicit decision from the user: confirm the proposed name or use
     their edit.
   - Create and switch to the new branch: `git checkout -b {new_name}`.
   - Leave the local `claude` branch as-is — do not reset it here. It will be
     fast-forwarded to main per the usual rule once this PR merges.

   If the current branch is not `claude`, skip this step.

1. Gather information:
   - Run `git status` to check working tree
   - Run `git diff main...HEAD` to see changes from main
   - Run `git log main..HEAD --oneline` to see commits on this branch
   - Check if branch tracks a remote with `git branch -vv`

2. Push branch to origin if needed (with `-u` flag)

3. Create PR using `gh pr create`:
   - Use a descriptive title summarizing the change
   - Include a summary section in the body

4. Save merge commit message to `local/merge.txt` in the format:
   ```
   PR #{pr_id} {branch_name}

   {optional one-line intro if needed}

   - bullet point per logical change
   - ...

   Closes #{issue} (if applicable)
   ```
   Where `branch_name` is the bare branch name (e.g., "fix-some-bug").
   Use bullet points for the body, not prose paragraphs.

5. Run `gh pr view --web {pr_id}`

6. Display the current contents of `local/merge.txt` in the response, inside a
   fenced code block, so it can be copied straight into the merge dialog.
   Read the file back from disk with the `Read` tool rather than reprinting
   what was written in step 4, so any hand edits since then are reflected.
