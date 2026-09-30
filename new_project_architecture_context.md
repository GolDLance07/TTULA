# Project Context — Actual Architecture

## Core Idea

We are modifying the existing Arsenal-NG project rather than building a separate application from scratch.

The main Arsenal-NG **TUI-based functionality remains**. We want to preserve and integrate its existing functionality, including its YAML-based cheatsheet/command system and command execution behavior.

The original Arsenal-NG YAML cheat files will be provided separately and must be treated as part of the project context.

## Tool Roles

### Arsenal-NG
- Integrate the existing Arsenal-NG functionality into our modified tool.
- Preserve its TUI.
- Preserve its YAML cheatsheet/command knowledge.
- Preserve its existing command retrieval and execution behavior where possible.
- Modify only what is necessary for integration.

### Tookie
- Keep Tookie's existing functionality.
- Do not unnecessarily rewrite its core behavior.
- It will handle the username/OSINT portion of the workflow.

### Uro
- Keep Uro's existing functionality.
- It will process/clean/normalize URLs produced by Tookie.

### Tailscale
Tailscale is where we add significant **new project-specific functionality**.

The tool will use the Tailscale network to connect to our controlled target/lab machine.

The intended workflow includes being able to:
- Connect to the target over the tailnet.
- Determine/reach the target web service.
- Open/interact with the target website through the tool's web/browser workflow.
- Use the connected target as the controlled environment for testing the integrated functionality.

Tailscale is therefore the connectivity layer, not an investigation mode.

## Overall Concept

```text
                    OUR MODIFIED TOOL
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
     Tookie               Uro             Arsenal-NG
     existing            existing          integrated
   functionality       functionality      functionality
                                             |
                                             v
                                       Commands / tools
                                             |
                                             v
                                         Tailscale
                                             |
                                             v
                                     Controlled Target
                                             |
                                             v
                                        Web Service
```

The project is essentially:

> **Tookie + Uro + full Arsenal-NG functionality + new Tailscale-based target/web functionality**

We are not creating a separate "Investigation Mode."

## Development Principle

Do not rebuild functionality that already exists.

First understand the original implementations, then integrate them with minimal unnecessary changes.

Priority:

1. Preserve Arsenal-NG's TUI.
2. Preserve Arsenal-NG's YAML cheats.
3. Preserve Tookie's functionality.
4. Preserve Uro's functionality.
5. Add the new Tailscale connectivity/web functionality.
6. Build the necessary glue between components.
7. Keep the system modular and testable in our controlled lab.
