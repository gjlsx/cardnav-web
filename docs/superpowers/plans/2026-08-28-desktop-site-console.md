# AI LoveMoney Desktop Site Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task-by-task. The authoritative TaskExec rows are `taskexec/cardnav-web/tasklist08281547.md` p011–p019 and their linked details.

**Goal:** Deliver the approved local Python/Tkinter console and a raw-to-public MySQL data pipeline without changing public routes or enabling unapproved network collection.

**Architecture:** Reuse the current Python collector as a small service layer. Add migration-safe MySQL tables for source, run, raw, staging and manual overrides; then connect a notebook-based Tkinter shell to those services. The publisher writes existing website runtime tables and its required snapshots atomically.

**Tech Stack:** Python 3.10+, Tkinter, MySQL `ailovemoney`, existing Astro/TypeScript public site, `unittest`, `pnpm`.

## Global Constraints

- Root tabs and collection child tabs are exactly those in the approved design.
- Source scheduling defaults: `enabled=false`, `interval_minutes=60`, `max_items_per_run=1000`; zero means unlimited.
- Site display score is independent of source priority; default sample score remains 50.
- Raw response retention is 30 days; never retain credentials or private/order data.
- A manual override/hide blocks staging and formal update for its stable key; cancelling it requires a new collection run.
- No production-host collection, SSH configuration editor, automatic source enablement or automated irreversible deployment.

## Execution Map

1. p011 locks the data and GUI contracts, including migration and record-key rules.
2. p012 adds migration-safe persistence and tests.
3. p013 implements capture, cleaning, override gates and formal publisher.
4. p014 establishes the reusable Tkinter shell, worker runner and per-tab log services.
5. p015–p018 implement the three root work areas and local scheduling, in dependency order.
6. p019 performs integration, actual GUI entry-point validation, documentation and focused refactor.

Every task has exact files, interfaces, tests and acceptance criteria in the corresponding TaskExec detail document. No task is allowed to start until its dependencies are `done`.
