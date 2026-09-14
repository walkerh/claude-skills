---
name: validate-worktree
description: Validate that the current environment meets Claude worktree requirements
---

# Validate Worktree

Run the validator using the Bash tool and report the results to the user:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/validate_worktree.sh"
```

`${CLAUDE_PLUGIN_ROOT}` resolves to this plugin's install directory, so the
script is found wherever the plugin was installed. The plugin's `bin/` is also
added to `PATH` when the plugin is enabled, so a bare `validate_worktree.sh`
works too; prefer the explicit form above, which does not depend on `PATH`
having been set up.

- If all checks pass, confirm that the environment is valid.
- If any checks fail, clearly list each failure so the user knows what to fix.
