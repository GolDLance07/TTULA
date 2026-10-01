# Implementation Brief — Web Crawler UI Update

## Objective

Update the existing security-tool interface with these changes:

1. Add an **Arsenal-style tool header/category system** for every integrated tool.{add the tages in every yaml file to there respective tool}
2. Rename **Secops Terminal Orchestrator** to **Web Crawler** everywhere in the visible UI.
3. Add a **Home** page as the first navigation item.
4. Redesign the visual system so the application is not dominated by blue.
5. Preserve existing functionality and tool integrations.

---

## 1. Application Identity

Use **Web Crawler** consistently in:

- Sidebar/navigation
- Home page
- Page titles
- Headers
- Empty states
- Help/documentation text
- Visible branding

Remove the visible name **Secops Terminal Orchestrator**.

---

## 2. Home Page

Add a new first navigation item:

**Home**

The page should contain:

### Web Crawler

A concise description:

> A unified security reconnaissance workspace for web crawling, identity discovery, URL processing, OSINT workflows, and security command knowledge.

### Created by

> **Created by**  
> Aarush Rahul Patel  
> Shreya Singh

Keep the page clean and concise. Do not turn it into a documentation page.

Suggested structure:

```text
WEB CRAWLER

Unified security reconnaissance workspace for web crawling,
identity discovery, URL processing and security operations.

Created by
Aarush Rahul Patel · Shreya Singh

[ Start Crawling ]    [ Explore Tools ]
```

Only add buttons if their destinations/actions already exist.

---

## 3. Arsenal-Style Tool Headers

Every tool page must have a reusable header containing:

```text
TOOL NAME

Short description

[Category] [Category] [Category]
```

This is inspired by Arsenal-NG's useful information architecture, **not a visual clone**.

Examples:

```text
TOOKIE

Username and identity OSINT tool

[OSINT] [IDENTITY DISCOVERY] [RECON]
```

```text
URO

URL normalization and deduplication utility

[WEB RECON] [URL PROCESSING] [RECON]
```

```text
ARSENAL-NG

Security command knowledge and operation reference

[RECON] [ENUMERATION] [EXPLOITATION] [WIRELESS SECURITY]
```

---

## 4. Tool Categories

Create a reusable category/tag system.

Initial category vocabulary:

- Recon
- OSINT
- Web Recon
- Network Recon
- Enumeration
- Identity Discovery
- URL Processing
- Service Enumeration
- Vulnerability Assessment
- Exploitation
- Post-Exploitation
- Wireless Security
- Authentication
- Credential Testing
- Digital Forensics
- Incident Response
- Information Gathering
- Command Reference
- Security Automation

Only show categories relevant to each tool. Do not give every tool every category.

---

## 5. Central Tool Metadata

Do not hardcode headers separately on every page.

Create one central metadata structure, adapting to the existing project architecture.

Example:

```python
TOOLS = {
    "tookie": {
        "name": "Tookie",
        "description": "Username and identity OSINT tool",
        "categories": ["OSINT", "Identity Discovery", "Recon"],
    },
    "uro": {
        "name": "Uro",
        "description": "URL normalization and deduplication utility",
        "categories": ["Web Recon", "URL Processing", "Recon"],
    },
    "arsenal": {
        "name": "Arsenal-NG",
        "description": "Security command knowledge and operation reference",
        "categories": [
            "Recon",
            "Enumeration",
            "Exploitation",
            "Wireless Security",
            "Command Reference",
        ],
    },
    "web_crawler": {
        "name": "Web Crawler",
        "description": "Web crawling and endpoint discovery",
        "categories": ["Web Recon", "Information Gathering", "Recon"],
    },
    "legba": {
        "name": "Legba",
        "description": "Multi-protocol authentication testing utility",
        "categories": ["Authentication", "Credential Testing"],
    },
}
```

Adjust descriptions/categories to match the actual implementation. Do not claim unsupported capabilities.

---

## 6. Category Badge Design

Use compact badges/chips.

Example:

```text
TOOKIE
Username and identity OSINT tool

[ OSINT ] [ IDENTITY DISCOVERY ] [ RECON ]
```

Requirements:

- Rounded but not excessively pill-shaped
- Strong contrast
- Small typography
- Easy scanning
- Avoid saturated blue for every badge
- Use restrained accent colors

---

## 7. Visual Redesign

The current UI should no longer feel like an entirely blue application.

Use a dark, modern cybersecurity palette.

### Base colors

```text
Background: #0B0F14
Surface:    #111820
Surface 2:  #17212B
Border:     #27323D
```

### Accent semantics

```text
Teal/Cyan → primary interactions
Violet    → OSINT/intelligence
Amber     → warnings/attention
Green     → successful operations
Red/Rose  → errors/high-risk actions
```

Do not use all accents everywhere. Use them semantically.

---

## 8. Subtle Tool Identity

Give tools a subtle accent identity:

```text
Web Crawler → cyan/teal
Tookie      → violet
Uro         → amber
Arsenal-NG  → green
Legba       → red/rose
```

Use accents only for:

- icons
- small header lines
- active navigation indicators
- badges
- small highlights

Do not make entire pages neon colors.

---

## 9. Navigation

Recommended structure:

```text
WEB CRAWLER
────────────────

⌂ Home

TOOLS
  Web Crawler
  Tookie
  Uro
  Arsenal-NG
  Legba
```

Only add other sections if they already exist as functional pages.

Do not create placeholder pages solely to fill the sidebar.

---

## 10. Active Tool State

When a tool is selected:

1. Highlight it in the sidebar.
2. Display its ToolHeader.
3. Display its description.
4. Display its category badges.
5. Keep the existing tool functionality below the header.

Example:

```text
WEB CRAWLER
Web crawling and endpoint discovery

[ WEB RECON ] [ INFORMATION GATHERING ] [ RECON ]

────────────────────────────────────

Target URL
[____________________________]

[ Start Crawl ]
```

---

## 11. Operation-Oriented Design

The category system should prepare the application for operation-based discovery later.

For example:

```text
Recon
Enumeration
Wireless Security
Exploitation
```

could eventually be used to filter relevant tools/operations.

For this implementation, build the metadata/components so this can be added later without restructuring the application.

Do not build a complex filtering system unless the existing code already supports it.

---

## 12. Responsive Design

Support common laptop and desktop widths.

- Desktop: expanded sidebar
- Smaller width: collapsible/compact sidebar
- Cards should resize instead of overflowing
- Long URLs/commands should wrap or scroll appropriately

---

## 13. Typography

Use a clean modern sans-serif.

Hierarchy:

```text
Application name → large/strong
Tool name         → large/bold
Description       → medium/muted
Category          → small/uppercase
Body              → normal
```

Use monospace only for:

- commands
- terminal output
- URLs
- IP addresses
- technical identifiers

---

## 14. Micro-interactions

Use subtle transitions:

- Sidebar selection
- Card hover
- Badge transitions
- Button hover
- Existing page transitions

Avoid excessive glow, flashing elements, or over-the-top cyberpunk styling.

The target is **professional security tooling**, not a 2004 hacker-movie interface.

---

## 15. Preserve Existing Functionality

Do not break:

- Web crawling
- Tookie
- Uro
- Arsenal-NG
- Legba
- Existing terminal/control mechanisms
- Existing data flow
- Existing command execution

This is primarily a UI and information-architecture update.

Before changing shared components, identify whether multiple tools depend on them.

Prefer reusable components.

---

## 16. Recommended Component Structure

Adapt this to the current framework rather than blindly creating a new architecture:

```text
components/
├── ToolHeader
├── CategoryBadge
├── ToolCard
├── Sidebar
├── HomePage
└── PageHeader
```

Central metadata can live in something like:

```text
config/
└── tools.py
```

Use the project's existing conventions if they differ.

---

## 17. Implementation Order

### Phase 1 — Rename

Replace the visible:

```text
Secops Terminal Orchestrator
```

with:

```text
Web Crawler
```

### Phase 2 — Tool metadata

Centralize:

- name
- description
- categories
- optional accent

### Phase 3 — ToolHeader

Create a reusable ToolHeader component.

### Phase 4 — Categories

Add relevant category badges to every tool.

### Phase 5 — Home

Add:

- Web Crawler title
- Short description
- Creator credits
- Existing valid primary actions

### Phase 6 — Visual redesign

Apply the new color system without changing functionality.

### Phase 7 — Responsive polish

Test common laptop/desktop widths.

### Phase 8 — Regression testing

Verify every existing tool still works.

---

## 18. Acceptance Criteria

- [ ] "Secops Terminal Orchestrator" no longer appears in the visible UI.
- [ ] Application is consistently branded **Web Crawler**.
- [ ] Home page exists and is the first navigation item.
- [ ] Home page contains a short Web Crawler description.
- [ ] Home page credits Aarush Rahul Patel and Shreya Singh.
- [ ] Every tool has a reusable Arsenal-style header.
- [ ] Every tool displays relevant categories.
- [ ] Categories are centrally defined.
- [ ] Interface is no longer dominated by blue.
- [ ] New palette uses restrained semantic accents.
- [ ] Existing functionality remains intact.
- [ ] Tool pages remain clean and readable.
- [ ] No unnecessary placeholder features/pages are added.
- [ ] UI works at common desktop/laptop widths.

---

## 19. Core Design Principle

Do **not** clone Arsenal-NG's UI.

Use the useful information architecture:

```text
Tool
 ↓
What does it do?
 ↓
What security domains does it belong to?
 ↓
What operations are relevant?
 ↓
What commands/actions are available?
```

Give Web Crawler its own visual identity and implementation.

The final result should feel like a polished, professional security-reconnaissance tool rather than a collection of unrelated pages.
