# Postala

Minimal Node/TypeScript test scripts for the [Runway Dev API](https://docs.dev.runwayml.com), using the official `@runwayml/sdk`.

## Setup

```bash
npm install
cp .env.example .env   # then put your key in RUNWAYML_API_SECRET
```

Get a key at https://dev.runway.com. `.env` is git-ignored; never commit the key.

## Scripts

| Command | What it does | Cost |
|---|---|---|
| `npm run check` | Prints the organization's credit balance and tier limits | Free |
| `npm run generate -- "prompt"` | Generates one 1600×1600 image with `muse_image`, waits for the task and saves it to `outputs/` | 1 credit |
| `npm run typecheck` | Type-checks `src/` | — |

Generated output URLs from Runway expire, which is why `generate` downloads a local copy.

## Claude Code cloud sessions

In a Claude Code cloud environment where `RUNWAYML_API_SECRET` is stored under **API credentials**, the key is added by the network proxy instead of an environment variable. Node must be told to use that proxy, and the SDK needs any placeholder value:

```bash
NODE_USE_ENV_PROXY=1 RUNWAYML_API_SECRET=proxy-injected npm run check
```

## Runway agent skills

`.agents/skills/` (symlinked into `.claude/skills/`) holds the `runway-dev` and `runway-dev-models` skills from `runwayml/skills`, installed with:

```bash
npx skills add runwayml/skills --skill runway-dev --skill runway-dev-models --agent cursor claude-code codex -y
```
