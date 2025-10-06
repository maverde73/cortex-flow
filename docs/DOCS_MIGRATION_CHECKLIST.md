# Documentation Migration Checklist

**Goal**: Consolidate all documentation into `docs/` with a unified structure and index.

**Status**: 🔄 IN PROGRESS

---

## Phase 1: Analysis & Planning ✅

### Checkpoint 1.1: Inventory Complete ✅
- [x] Listed all .md files in project
- [x] Identified documentation categories
- [x] Created migration checklist

### Documentation Inventory

**Root Level Files** (22 files total):
1. `README.md` → **KEEP** (main entry point)
2. `CLAUDE.md` → Migrate to `docs/development/`
3. `SETUP.md` → Migrate to `docs/getting-started/`
4. `EXAMPLES.md` → Merge into workflows cookbook
5. `RELEASE_NOTES.md` → Migrate to `docs/`
6. `AGENT_MANAGEMENT.md` → Migrate to `docs/agents/`
7. `IMPLEMENTATION_SUMMARY.md` → Migrate to `docs/architecture/`
8. `REACT_IMPLEMENTATION_CHECKLIST.md` → Migrate to `docs/agents/`
9. `MCP_INTEGRATION_TEST_SUMMARY.md` → Migrate to `docs/mcp/`
10. `MCP_MANUAL_PROMPTS_TEST_REPORT.md` → Migrate to `docs/mcp/`

**docs/ Folder** (Already organized):
- `docs/Architettura Backend per Agenti Configurabili.md` → Keep, rename
- `docs/Guida Agenti ReAct Multi-MCP LangChain.md` → Keep, rename
- `docs/GUIDA_FUNZIONALITA.md` → Merge into main docs
- `docs/PROJECT_OVERVIEW.md` → Merge into README
- `docs/REACT_CONTROLS.md` → Migrate to `docs/agents/`
- `docs/workflows/*` → Already organized, verify completeness

**Other Locations**:
- `scripts/README.md` → Migrate to `docs/development/`
- `tests/README.md` → Migrate to `docs/development/`

---

## Phase 2: Create Unified Structure 🔄

### Checkpoint 2.1: Create docs/ Structure
- [ ] Create `docs/README.md` (main index)
- [ ] Create `docs/getting-started/`
- [ ] Create `docs/architecture/`
- [ ] Create `docs/agents/`
- [ ] Create `docs/mcp/`
- [ ] Create `docs/workflows/` (already exists, verify)
- [ ] Create `docs/development/`
- [ ] Create `docs/reference/`

### Checkpoint 2.2: Design Documentation Structure
```
docs/
├── README.md                          # Main documentation index
├── RELEASE_NOTES.md                   # Version history
│
├── getting-started/
│   ├── README.md                      # Quick start guide
│   ├── installation.md                # From SETUP.md
│   ├── configuration.md               # Environment variables
│   └── first-workflow.md              # Hello world example
│
├── architecture/
│   ├── README.md                      # Architecture overview
│   ├── backend-design.md              # From "Architettura Backend"
│   ├── multi-agent-system.md          # From "Guida Agenti ReAct"
│   ├── implementation-summary.md      # From IMPLEMENTATION_SUMMARY.md
│   └── project-structure.md           # File organization
│
├── agents/
│   ├── README.md                      # Agents overview
│   ├── supervisor.md                  # Supervisor agent
│   ├── react-pattern.md               # ReAct implementation
│   ├── react-controls.md              # From REACT_CONTROLS.md
│   ├── agent-management.md            # From AGENT_MANAGEMENT.md
│   ├── factory.md                     # Agent factory pattern
│   └── implementation-checklist.md    # From REACT_IMPLEMENTATION_CHECKLIST.md
│
├── mcp/
│   ├── README.md                      # MCP integration overview
│   ├── getting-started.md             # Quick start with MCP
│   ├── protocol-implementation.md     # From MCP_INTEGRATION_TEST_SUMMARY.md
│   ├── manual-prompts.md              # From MCP_MANUAL_PROMPTS_TEST_REPORT.md
│   ├── configuration.md               # MCP server config
│   ├── testing.md                     # MCP testing guide
│   └── troubleshooting.md             # Common issues
│
├── workflows/
│   ├── README.md                      # Already exists
│   ├── 01_creating_templates.md       # Already exists
│   ├── 02_conditional_routing.md      # Already exists
│   ├── 03_mcp_integration.md          # Already exists
│   ├── 04_visual_diagrams.md          # Already exists
│   ├── 05_cookbook.md                 # Already exists + EXAMPLES.md
│   ├── 06_migration_guide.md          # Already exists
│   └── examples/                      # Already exists
│
├── development/
│   ├── README.md                      # Development guide
│   ├── contributing.md                # How to contribute
│   ├── claude-code.md                 # From CLAUDE.md
│   ├── scripts.md                     # From scripts/README.md
│   ├── testing.md                     # From tests/README.md
│   └── project-guidelines.md          # File placement rules
│
└── reference/
    ├── README.md                      # API reference index
    ├── configuration.md               # All config options
    ├── environment-variables.md       # Complete .env reference
    ├── api.md                         # REST API endpoints
    └── cli.md                         # Command-line tools
```

---

## Phase 3: Migration by Category

### Checkpoint 3.1: Getting Started Docs
- [ ] Create `docs/getting-started/README.md`
- [ ] Migrate SETUP.md → `docs/getting-started/installation.md`
- [ ] Extract config from SETUP.md → `docs/getting-started/configuration.md`
- [ ] Create `docs/getting-started/first-workflow.md`
- [ ] Verify all content migrated
- [ ] Delete SETUP.md

### Checkpoint 3.2: Architecture Docs
- [ ] Create `docs/architecture/README.md`
- [ ] Migrate `docs/Architettura Backend...` → `docs/architecture/backend-design.md`
- [ ] Migrate `docs/Guida Agenti ReAct...` → `docs/architecture/multi-agent-system.md`
- [ ] Migrate IMPLEMENTATION_SUMMARY.md → `docs/architecture/implementation-summary.md`
- [ ] Merge PROJECT_OVERVIEW.md content
- [ ] Create `docs/architecture/project-structure.md`
- [ ] Verify all content migrated
- [ ] Delete old files

### Checkpoint 3.3: Agents Docs
- [ ] Create `docs/agents/README.md`
- [ ] Migrate AGENT_MANAGEMENT.md → `docs/agents/agent-management.md`
- [ ] Migrate REACT_CONTROLS.md → `docs/agents/react-controls.md`
- [ ] Migrate REACT_IMPLEMENTATION_CHECKLIST.md → `docs/agents/implementation-checklist.md`
- [ ] Extract supervisor docs → `docs/agents/supervisor.md`
- [ ] Extract ReAct pattern → `docs/agents/react-pattern.md`
- [ ] Extract factory pattern → `docs/agents/factory.md`
- [ ] Verify all content migrated
- [ ] Delete old files

### Checkpoint 3.4: MCP Docs
- [ ] Create `docs/mcp/README.md`
- [ ] Create `docs/mcp/getting-started.md`
- [ ] Migrate MCP_INTEGRATION_TEST_SUMMARY.md → `docs/mcp/protocol-implementation.md`
- [ ] Migrate MCP_MANUAL_PROMPTS_TEST_REPORT.md → `docs/mcp/manual-prompts.md`
- [ ] Extract configuration → `docs/mcp/configuration.md`
- [ ] Extract testing guide → `docs/mcp/testing.md`
- [ ] Create `docs/mcp/troubleshooting.md`
- [ ] Verify all content migrated
- [ ] Delete old files

### Checkpoint 3.5: Workflows Docs
- [ ] Verify `docs/workflows/README.md` is complete
- [ ] Merge EXAMPLES.md → `docs/workflows/05_cookbook.md`
- [ ] Verify all 6 guides are complete
- [ ] Verify examples directory
- [ ] Update cross-references
- [ ] Delete EXAMPLES.md

### Checkpoint 3.6: Development Docs
- [ ] Create `docs/development/README.md`
- [ ] Migrate CLAUDE.md → `docs/development/claude-code.md`
- [ ] Migrate scripts/README.md → `docs/development/scripts.md`
- [ ] Migrate tests/README.md → `docs/development/testing.md`
- [ ] Extract CLAUDE.md rules → `docs/development/project-guidelines.md`
- [ ] Create `docs/development/contributing.md`
- [ ] Verify all content migrated
- [ ] Delete old files (keep minimal scripts/README.md, tests/README.md)

### Checkpoint 3.7: Reference Docs
- [ ] Create `docs/reference/README.md`
- [ ] Extract all config → `docs/reference/configuration.md`
- [ ] Create complete env vars reference → `docs/reference/environment-variables.md`
- [ ] Document REST API → `docs/reference/api.md`
- [ ] Document CLI tools → `docs/reference/cli.md`
- [ ] Verify completeness

---

## Phase 4: Main Documentation Files

### Checkpoint 4.1: Create Master Index
- [ ] Create comprehensive `docs/README.md`
- [ ] Link to all sections
- [ ] Add quick navigation
- [ ] Add visual diagrams/flowcharts
- [ ] Add "What to read first" guide

### Checkpoint 4.2: Migrate Release Notes
- [ ] Move RELEASE_NOTES.md → `docs/RELEASE_NOTES.md`
- [ ] Verify changelog format
- [ ] Add version links

### Checkpoint 4.3: Update Root README
- [ ] Update README.md with docs/ links
- [ ] Add badges (if any)
- [ ] Simplify to quick start + link to docs
- [ ] Add visual overview
- [ ] Link to docs/getting-started/

---

## Phase 5: Verification & Cleanup

### Checkpoint 5.1: Content Verification
- [ ] Read through entire `docs/` tree
- [ ] Check for broken internal links
- [ ] Check for missing content
- [ ] Verify all examples still work
- [ ] Verify all code references are correct

### Checkpoint 5.2: Cross-Reference Check
- [ ] Verify all docs link to each other correctly
- [ ] Update navigation in each README
- [ ] Add breadcrumbs where helpful
- [ ] Add "See also" sections

### Checkpoint 5.3: Remove Old Files
**ONLY after verification complete!**
- [ ] Delete SETUP.md
- [ ] Delete EXAMPLES.md
- [ ] Delete AGENT_MANAGEMENT.md
- [ ] Delete IMPLEMENTATION_SUMMARY.md
- [ ] Delete REACT_IMPLEMENTATION_CHECKLIST.md
- [ ] Delete MCP_INTEGRATION_TEST_SUMMARY.md
- [ ] Delete MCP_MANUAL_PROMPTS_TEST_REPORT.md
- [ ] Delete `docs/Architettura Backend per Agenti Configurabili.md`
- [ ] Delete `docs/Guida Agenti ReAct Multi-MCP LangChain.md`
- [ ] Delete `docs/GUIDA_FUNZIONALITA.md`
- [ ] Delete `docs/PROJECT_OVERVIEW.md`
- [ ] Delete `docs/REACT_CONTROLS.md`
- [ ] Clean up scripts/README.md (keep minimal)
- [ ] Clean up tests/README.md (keep minimal)

### Checkpoint 5.4: Final Review
- [ ] Read README.md → Should lead to docs
- [ ] Read docs/README.md → Should cover everything
- [ ] Test all example commands
- [ ] Check all file paths in docs
- [ ] Run spell check
- [ ] Verify markdown formatting

---

## Phase 6: Maintenance Setup

### Checkpoint 6.1: Create Documentation Standards
- [ ] Add docs/CONTRIBUTING.md with doc standards
- [ ] Document markdown style guide
- [ ] Document file naming conventions
- [ ] Add doc review checklist

### Checkpoint 6.2: Add Navigation Helpers
- [ ] Add Table of Contents to long docs
- [ ] Add "Back to top" links
- [ ] Add consistent headers/footers
- [ ] Add visual guides where helpful

---

## Progress Tracking

### Current Session Completed:
- [x] Phase 1: Analysis & Planning
- [ ] Phase 2: Create Unified Structure
- [ ] Phase 3: Migration by Category
- [ ] Phase 4: Main Documentation Files
- [ ] Phase 5: Verification & Cleanup
- [ ] Phase 6: Maintenance Setup

### Next Session Start Point:
**Checkpoint 2.1** - Create docs/ structure directories

---

## Notes & Decisions

### Naming Conventions Decided:
- Use lowercase with hyphens: `getting-started.md` not `Getting_Started.md`
- Be descriptive: `manual-prompts.md` not `prompts.md`
- Group by topic in folders

### Content Decisions:
- Keep README.md minimal, link to docs/
- CLAUDE.md stays, but also copied to docs/development/
- RELEASE_NOTES.md moves to docs/ but keeps visibility
- Scripts/tests keep minimal READMEs with "See docs/development/"

### What Gets Deleted vs Kept:
- DELETE: Duplicated content now in docs/
- KEEP: README.md (root), CLAUDE.md (project instructions)
- KEEP: .pytest_cache/README.md (pytest generated)

---

## Validation Criteria

Before marking complete:
1. ✅ All documentation in `docs/` with clear hierarchy
2. ✅ Master index at `docs/README.md` covers everything
3. ✅ No broken links
4. ✅ No lost information from old files
5. ✅ README.md points to docs/
6. ✅ Old files deleted (except keepers)
7. ✅ All examples tested and work
8. ✅ File organization follows CLAUDE.md rules

---

**Last Updated**: 2025-10-06
**Current Phase**: Phase 1 Complete, Starting Phase 2
