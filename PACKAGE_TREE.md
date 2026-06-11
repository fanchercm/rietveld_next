# Clean Codex Package Tree

This package uses simple canonical names and an expanded prompt set.

```text
rietveld_next_codex_prompt_expanded/
├── AGENTS.md
├── README.md
├── MANIFEST.json
├── PACKAGE_TREE.md
├── architecture/
├── backlog/
│   ├── issues.md
│   ├── issues.json
│   ├── issues.csv
│   ├── milestones.md
│   ├── milestones.json
│   └── milestones.csv
├── github/
│   ├── issues_import.json
│   └── milestones_import.json
├── schemas/
│   └── project.schema.json
├── prompts/
│   ├── README.md
│   ├── program/
│   ├── milestones/        # 40 milestone prompts
│   ├── issues/            # 327 issue prompts
│   ├── workstreams/       # 19 workstream prompts
│   └── legacy/            # retained earlier prompts
├── scaffold/
├── validation/
└── docs/
```

Canonical backlog files remain `backlog/issues.*` and `backlog/milestones.*`. GitHub import files remain `github/issues_import.json` and `github/milestones_import.json`.
