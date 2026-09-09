# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python standard library HTTP server, custom MiniDB core, SQLite-based independent library demo, and native HTML/CSS/JavaScript. The stack minimizes setup for a one-week training project.

## Users

Primary users are a three-person student team. Responsibilities follow the three course modules: SQL compiler, operating-system storage, and database engine. Teachers may use hidden tests, random code explanation, live modification, and debugging.

## Product Purpose

Provide an inspectable teaching MiniDB that connects compiler theory, operating-system storage mechanisms, and database execution from SQL text through physical disk pages.

## Positioning

The MiniDB core owns lexing, parsing, AST, semantics, plans, optimization, row encoding, pages, buffering and execution. The separate library demo uses SQLite and must not be presented as the MiniDB storage path.

## Operating Context

Used locally on a student computer for development, classroom demonstration, assessment, and report screenshots. The main workflow is registering books and readers, lending available copies, returning loans, and reviewing status statistics.

## Capabilities and Constraints

- Manage books and readers with search and status filtering.
- Create and complete loan records while maintaining book inventory in a transaction.
- Show dashboard totals and recent activity.
- Seed realistic illustrative data and reset the local database safely.
- Run without a separately installed database server or third-party Python packages.
- Deliver source code, architecture and grammar documentation, test evidence, three-person division notes, and a one-week practicum report.

## Evidence on Hand

No external brand assets, institutional claims, or production data were supplied. All bundled people, books, identifiers, and metrics are explicitly illustrative.

## Product Principles

- Make relational database concepts inspectable.
- Keep the core borrow/return workflow dependable and easy to demonstrate.
- Prefer clear tables and direct actions over decorative dashboard patterns.
- Make setup and reset predictable on a classroom computer.
- Keep documentation aligned with the running implementation.

## Accessibility & Inclusion

Support keyboard navigation, visible focus, readable contrast, reduced motion, responsive layouts, and clear Chinese labels and error recovery.
