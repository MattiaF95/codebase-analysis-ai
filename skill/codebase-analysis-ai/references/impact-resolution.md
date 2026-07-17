# Impact resolution

Use `docs/_meta/documentation-map.json` as the source-to-document graph.

## Algorithm

1. Match each changed path against explicit sources and source patterns.
2. Collect directly mapped document IDs.
3. Add each direct document's `relatedDocuments` exactly once.
4. Stop. Do not inspect relationships belonging only to the added related documents.
5. Validate hashes for changed sources and existence for every impacted document path.

Return direct and related impacts separately so the agent can prioritize edits over consistency checks.

Deleted and renamed files require mapping maintenance. New relevant files that match no rule must be reported as unmapped rather than ignored.
