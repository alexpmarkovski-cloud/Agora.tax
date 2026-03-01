---
title: "Database Safety"
description: "Guidelines and restrictions for interacting with the OG Agora database."
---

# Database Safety & Constraints

To ensure data integrity and prevent accidental data loss or corruption, follow these strict rules when working with the OG Agora database (SQLite for local, PostgreSQL for production).

## CRITICAL RULE: No Unauthorized Edits
> [!CAUTION]
> **NEVER** edit the database schema or modify existing data unless explicitly and specifically instructed by the user to do so for a particular task.

## Guidelines for Database Interactions

### Schema Changes
1. **Always Propose First**: If you believe a schema change is necessary, include it in an `implementation_plan.md` and wait for user approval.
2. **Use Migrations**: Always use Django migrations (`makemigrations`, `migrate`) to modify the schema. Never attempt direct SQL queries for schema changes.
3. **Verify Locally**: Test migrations on the local `db.sqlite3` before proposing any changes that might affect production.

### Data Manipulation
1. **Read-Only by Default**: Assume a read-only stance towards the data. Use the `view_file` tool on `models.py` or administrative views to understand the data structure.
2. **Batch Operations**: If instructed to update data, use Django's QuerySet API (e.g., `update()`, `bulk_create()`) rather than iterating and saving individual instances where performance is a concern.
3. **Backups**: Before performing significant data operations (if instructed), remind the user to ensure they have a recent backup of `db.sqlite3`.

## Verification Steps
- Run `python manage.py check` to ensure no model issues.
- Verify that `models.py` matches the expected state of the database.
