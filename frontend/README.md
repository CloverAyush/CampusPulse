# CampusPulse — frontend

Next.js App Router, TypeScript, Tailwind. The API it talks to lives in `../backend`.

```bash
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_URL
npm run dev
```

Checks, both of which gate CI:

```bash
npx tsc --noEmit
npx eslint src
```

Setup, architecture and the product rules are in the root [README](../README.md).

## Layout

- `src/app/` — routes. `login`, `report`, `my-reports`, `handler`, `higher-authority`, `admin`, `issues/[id]`.
- `src/components/` — shared UI, including the loading, empty and error states every page uses.
- `src/lib/` — `api.ts` (typed client with a timeout and a single session-expiry path), `auth.tsx` (session context), `format.ts` (dates, labels, the https link guard).

Two conventions worth knowing before you add a page:

- **A failed load must never look like an empty list.** Use `ErrorState`, not a
  silent fallback. A handler seeing "nothing assigned" when the API is down is the
  bug this codebase most wants to avoid.
- **Data loads live inside the effect** with a `cancelled` guard, and reloads go
  through a token, so a slow response cannot overwrite a newer one.
