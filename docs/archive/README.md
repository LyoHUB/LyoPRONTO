# Documentation Archive

This directory contains detailed session summaries and historical documentation from the development process.

## Archived Files

These files document the step-by-step development process but have been superseded by more concise documentation in the parent directory.

### Session Summaries
- `TESTING_SUMMARY.md` - Initial testing infrastructure setup
- `TEST_FIXES_SUMMARY.md` - Bug fixes and debugging during testing
- `TESTING_AND_EXAMPLES_SUMMARY.md` - Web interface implementation progress
- `OPTIMIZER_TESTING_SUMMARY.md` - Detailed optimizer testing documentation
- `OPTIMIZER_COMPLETE.md` - Optimizer implementation completion summary
- `DESIGN_SPACE_COMPLETE.md` - Design space generator completion summary
- `TESTING_AND_EXAMPLES_COMPLETE.md` - Overall testing completion
- `WEB_INTERFACE_COMPLETE.md` - Final web interface parity summary

### Organization Documents
- `REORGANIZATION_COMPLETE.md` - Repository cleanup and organization
- `REPOSITORY_ORGANIZATION.md` - File structure organization
- `CODE_STRUCTURE.md` - Code organization (superseded by ARCHITECTURE.md)
- `README_TESTING.md` - Testing documentation (superseded by tests/README.md)

## Why Archived?

These documents were created during iterative development sessions and contain:
- Detailed chronological progress logs
- Step-by-step debugging narratives  
- Session-specific context and decisions
- Redundant information across multiple files

While valuable for understanding the development process, they made the repository cluttered with too many top-level documentation files.

## Current Documentation

For current, consolidated documentation, see the parent `docs/` directory:
- `DEVELOPMENT_LOG.md` - High-level chronological summary (replaces session summaries)
- `ARCHITECTURE.md` - System architecture
- `PHYSICS_REFERENCE.md` - Physics equations and models
- `COEXISTENCE_PHILOSOPHY.md` - Scipy/Pyomo coexistence strategy
- `PYOMO_ROADMAP.md` - Pyomo integration plan
- `GETTING_STARTED.md` - Developer onboarding

And in the repository root:
- `README.md` - Main entry point
- `CONTRIBUTING.md` - Contribution guidelines

## Using These Files

These archived files are kept for:
1. **Historical reference** - Understanding why decisions were made
2. **Detailed examples** - More verbose explanations of features
3. **Troubleshooting** - Similar issues encountered during development

If you need very detailed information about a specific implementation (optimizer, design space, etc.), these files contain extensive step-by-step documentation.

---

**Archived**: October 2, 2025  
**Reason**: Repository documentation consolidation  
**Replacement**: `docs/DEVELOPMENT_LOG.md` + core documentation files
