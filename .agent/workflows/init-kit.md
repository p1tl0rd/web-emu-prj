---
description: Initialize the Universal Agent Kit (Load Rules & Skills)
---

This workflow forces the agent to index all Universal Rules and Skills contained in the `.agent` directory.
Run this command ONCE when you first copy the kit into a new project, or whenever you update the kit manually.

1.  **Index Rules:**
    -   Use `find_by_name` (or `list_dir`) to list all markdown files (`.md`) in the `.agent/rules` directory.
    -   For *each* file found, use `view_file` (or `read_resource`) to read its full content.
    -   *Goal:* Ingest all governance rules (Identity, Standards, etc.) into your context.

2.  **Index Skills:**
    -   Use `find_by_name` to look for all files named `SKILL.md` inside `.agent/skills` (recursive).
    -   For *each* `SKILL.md` found, use `view_file` to read it.
    -   *Goal:* Understand all available capabilities (CLI, Docker, Git, etc.).

3.  **Confirmation:**
    -   After reading all files, confirm to the user: "Universal Rules and Skills have been loaded successfully."
    -   List the number of Rule files and Skill files you just read.
