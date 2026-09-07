# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated by the user: Python standard library HTTP server, SQLite, and native HTML/CSS/JavaScript. The stack minimizes setup and keeps database concepts visible for a two-week training project.

## Users

Primary users are a two-person student team completing and defending a systems practicum. Teachers evaluate the team through hidden tests, random code explanation, live modification, and debugging. The original reading-room interface remains an upper-layer demonstration.

## Product Purpose

Provide an inspectable teaching MiniDB that connects compiler theory, operating-system storage mechanisms, and database execution from SQL text through physical disk pages.

## Positioning

Unlike a CRUD application backed by SQLite, the MiniDB core owns lexing, parsing, AST, semantics, plans, optimization, row encoding, pages, buffering, execution, locks, and authorization; every stage can be inspected during a classroom defense.

## Operating Context

Used locally on a student computer for development, classroom demonstration, assessment, and report screenshots. The main workflow is registering books and readers, lending available copies, returning loans, and reviewing status statistics.

## Capabilities and Constraints

- Manage books and readers with search and status filtering.
- Create and complete loan records while maintaining book inventory in a transaction.
- Show dashboard totals and recent activity.
- Seed realistic illustrative data and reset the local database safely.
- Run without a separately installed database server or third-party Python packages.
- Deliver source code, ER diagram, database design, API notes, test notes, and a two-week practicum report.

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
