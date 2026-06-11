# Codex Prompt: Implement Milestones Against Seed Issues

Use `backlog/milestones_100.json` as the canonical implementation plan. Each milestone maps to exactly one seed issue in `backlog/github_issues.json`.

For a selected milestone:

1. Read `matching_issue_number`, `scope`, `deliverables`, `depends_on_milestones`, and `acceptance_criteria`.
2. Verify dependencies are complete or explicitly mark the work as blocked.
3. Make the smallest coherent code/doc/test change that satisfies the milestone.
4. Update or add tests according to the milestone acceptance criteria.
5. Update docs, schema examples, provenance behavior, or API docs if the change affects them.
6. Produce a closing note that references both the milestone ID and matching issue number.

Do not broaden scope beyond the matching issue unless required to satisfy a declared dependency or acceptance criterion.
