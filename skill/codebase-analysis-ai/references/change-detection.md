# Change detection

Resolve changes in this order:

1. Explicit commit or commit range supplied by the user.
2. Staged, unstaged, and untracked working-tree changes.
3. `lastProcessedCommit..HEAD` when a valid shared baseline exists.
4. `HEAD^..HEAD` for a clean repository without a baseline.

For CI, read the event payload:

- Pull Request: base SHA to head SHA.
- Push: before SHA to after SHA.
- Merge group: merge-group base SHA to head SHA.
- Manual dispatch: explicit inputs or previous commit to HEAD.

Handle add, modify, delete, rename, and copy statuses. Treat production files that match no mapping as unmapped evidence requiring classification. Ignore generated output, dependencies, secrets, and configured exclusions.

For the first push of a new ref, inspect every commit reachable from the pushed tip that is not already reachable from a remote ref. Never reduce a multi-commit branch to the tip commit alone.

Content hashes are authoritative for synchronization. Commit IDs are informative baselines and must not be the only freshness signal.
