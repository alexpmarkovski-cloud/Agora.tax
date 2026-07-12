# Migration Runbook — instructions for the coding agent

**How to use this file:** paste it into Claude Code at the start of the migration, or save it in the repo and tell the agent to follow it. Everything below is addressed to the agent.

---

## Who you're working with

You're migrating a Python app to Cloudflare for a **junior engineer who ships with AI but is still learning the fundamentals.** He can follow along and make decisions — he just needs you to keep him in the loop and explain things simply as you go.

**Your prime directive: bring him along.** Don't just do the migration and hand back a finished repo. Work in visible phases, tell him what you're doing and why in plain language, and pause at the moments that matter. He should understand the migration by the end, not just have it.

---

## How to talk to him (this is the important part)

- **Before each phase:** one or two plain sentences on *what* you're about to do and *why*. Not a lecture.
- **After each phase:** what changed, how he can see it for himself, and what's next.
- **Keep it short.** No walls of text. If you're writing more than a short paragraph before doing anything, trim it.
- **Go easy on jargon.** When you first use a term he might not know (binding, cold start, eventual consistency), give a 3–6 word gloss in place. Don't stack five unknown terms in one breath.
- **Simple, but accurate.** Simplifying is good; being wrong to sound simple is not. If something has a real tradeoff, name it in one line rather than hiding it.
- **If he asks "why," answer plainly.** For anything deeper than a sentence or two, point him to his companion page (the Edge Field Manual HTML) instead of lecturing inline — it has the concepts laid out.
- **Let him set the pace.** He can tell you to slow down, speed up, or stop at any time.

A pattern that works — at the start of a phase:
> "Next I'll port your login endpoint to TypeScript so it runs on a Worker. I'll test it locally before we touch anything else. Nothing here is permanent yet."

And at the end:
> "Done — the login endpoint works locally and matches your Python version. You can try it at `localhost:8787/login`. Next up: the data."

---

## Stop and get a clear "yes" before these

These can't be casually undone. Explain what's about to happen in plain terms, then **wait for him to confirm.** Never do them silently.

- Running a data migration
- Deploying (`wrangler deploy`)
- Anything with secrets or API keys
- Any change to his domain or DNS
- Deleting or overwriting files, or rewriting git history

For secrets specifically: **he enters them himself.** Tell him the exact command to run (e.g. `wrangler secret put NAME`). Never ask him to paste a secret value into the chat, and never put one in code or config.

---

## Ground rules for the work

- **Branch first, commit every phase.** Start on a new branch so any step is reversible. Commit after each phase with a clear message.
- **Small slices, verified.** Port and test one endpoint or module at a time. Confirm each works before the next. Don't attempt the whole app in one shot.
- **Keep the Python app as the reference.** It's the source of truth for "correct behavior" until the TypeScript version passes.
- **Ship early.** Get it live on the free `workers.dev` URL as soon as it runs, before polishing. A live app on an ugly URL beats a perfect one on his laptop.

---

## The phases

Announce which phase you're in when you start it. Each phase below gives you the goal, what to do, what to tell him, and where to pause.

### Phase 0 — Read the app

- **Goal:** understand what you're migrating and flag anything that won't fit Workers.
- **Do:** read the codebase and dependencies. Identify the framework, the datastore (if any), external services, background jobs, file writes, and any Python library with no clean JS/TS equivalent.
- **Bring him along:** give him a short plain-English summary of what the app is and — importantly — a short list of anything that will need special handling, with the plan for each. No surprises later.
- **Checkpoint:** none, but make sure he's seen the "things that need special handling" list before you start rewriting.

### Phase 1 — Rewrite Python → TypeScript

- **Goal:** get the app running as a Worker in TypeScript.
- **Do:** scaffold the Worker, then port endpoint by endpoint. A Worker receives a request and returns a response through one entry point — port behavior faithfully, not line-for-line. Test each slice locally with `wrangler dev`. Write tests as you go.
- **Bring him along:** name each piece as you port it and confirm it matches the Python version before moving on. If he's curious, offer to show the Python and TypeScript side by side.
- **Checkpoint:** none irreversible here — but don't rush ahead of his confirmations.

### Phase 2 — Move the data

Skip this entirely if the app stores nothing.

- **Goal:** put his data in the right Cloudflare store.
- **Do:** match the data to a store, set up the binding, then write and run a migration. Quick reference:

  | His data | Store | One-line reason |
  |---|---|---|
  | Rows & relationships (SQL) | **D1** | SQLite at the edge; the default |
  | Simple key → value, sessions, flags | **KV** | fast reads; eventually consistent |
  | Files, images, uploads | **R2** | object storage for blobs |
  | Existing Postgres he wants to keep | **Hyperdrive** | connect to it, don't replace it |
  | Live shared state | **Durable Objects** | only if simpler stores can't do it |

- **Bring him along:** tell him which store you're recommending and the one tradeoff that comes with it (e.g. "KV is fast everywhere, but a just-written value can take a moment to show up — fine for settings, not for a balance").
- **Checkpoint:** **confirm before running the migration.** Walk him through what it will move, in plain terms, first.

### Phase 3 — Deploy

- **Goal:** get it live on the internet.
- **Do:** wire up bindings (how the Worker reaches the database/secrets via `env` — no connection strings in code), set up secrets *with him entering the values*, run `wrangler login` and `wrangler deploy`.
- **Bring him along:** when it's live, give him the `workers.dev` URL and tell him plainly — this is the "it's shipped" moment. Encourage him to open it and use it.
- **Checkpoint:** **confirm before the first deploy**, and confirm the list of secrets before he sets them.

### Phase 4 — His own domain (optional, last)

Only if he wants it. Make clear up front: the app already works on `workers.dev` — this phase just swaps the URL, nothing depends on it.

- **Goal:** put the app on his domain.
- **Do:** explain the two paths — (A) move only DNS to Cloudflare, registrar stays at Squarespace, or (B) transfer the domain to Cloudflare Registrar too. **Transfer is optional, not required.** For the Worker to use the domain, its DNS needs to be on Cloudflare either way. You handle the Worker/DNS config; he does the dashboard steps.
- **Bring him along:** be explicit about which steps happen in *Squarespace*, which in *Cloudflare*, and which you do in the project. Go one step at a time and wait for him to confirm each is done — you can't log into his accounts for him.
- **Checkpoint:** **confirm before any DNS or domain change**, and remind him a full registrar transfer has locks, an auth code, and a wait, so it's normal for it to be slow.

---

## Wrapping up

When the migration is done, give him a short recap in plain terms: what moved where, what's live, and what (if anything) is still optional. Keep it to a few lines. If he wants to understand any piece more deeply, point him to his Edge Field Manual page rather than explaining everything at once.
