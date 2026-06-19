# React Workflows

Frontend structure conventions for React/TSX work. **Opt-in** — install this plugin only when you're working on a React project, so it doesn't fire during backend/CRM/Dataverse work.

## Why a separate plugin

The skill inside (`react-structure`) triggers aggressively on *any* React/TSX work — even "add a button". The other plugins in this marketplace (`dev-workflows`, `ado-backlog`, `github-backlog`) are daily/backend/CRM oriented and stay enabled all the time. Bundling a React skill into those would make it fire everywhere. Keeping it as its own plugin means it's only active when you explicitly enable it for a frontend project.

## Skills

- **react-structure** — Enforces per-component file separation:
  - `ComponentName.tsx` — UI / JSX only
  - `useComponentName.ts` — hooks, handlers, Redux, business logic
  - `type.ts` — component-scoped types
  - `componentSlice.ts` — Redux Toolkit slice (only if the component owns state)

  Stack: TypeScript (strict) + Redux Toolkit + MUI + `@mui/x-data-grid-premium`. Requires a Mermaid flowchart of the data/function flow before any code is written.

## Install / enable

This plugin lives in the `workflow-daily-work` marketplace (repo root). To turn it on **only** for a React project, enable it from that project:

```
/plugin
```

…then enable `react-workflows`. Disable it again when you switch back to backend/CRM work.
