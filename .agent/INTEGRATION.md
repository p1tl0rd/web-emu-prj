# Universal Agent Kit Integration Guide

This guide explains how to add the **Universal Agent Kit** (Rules, Skills, Workflows) to any project.

## Method: Copy & Bootstrap

This method is "Self-Contained". The kit becomes part of your project and doesn't depend on external paths.

### Step 1: Copy the Kit
Copy the entire `.agent` folder from this repository into the **root** of your target project.

> **Note:** If your project already has an `.agent` folder, you can merge the contents.
> - Ensure `.agent/rules` is populated.
> - Ensure `.agent/skills` is populated.
> - Ensure `.agent/workflows` contains `init-kit.md`.

### Step 2: Initialize (Load Rules)
Open your project in the IDE with the Agent.
In the chat, run the following command **once**:

```
/init-kit
```

The agent will read all the rule files and skill definitions.

### How it works
- The `/init-kit` command triggers a workflow that tells the agent to scan `.agent/rules` and `.agent/skills`.
- By reading these files, the agent "learns" the Universal Standards (Identity, Tech Specs, Communication) and registers the Skills (CLI, Docker, Git, etc.).

### When to update
If you want to update the kit to a newer version:
1.  Overwrite the `.agent` folder with the new files.
2.  Run `/init-kit` again to refresh the agent's memory.
