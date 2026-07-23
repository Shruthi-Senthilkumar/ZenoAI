# ZenoAI Web — Next.js migration

Tech stack per Frontend Spec / PRD: Next.js (App Router, TS) + Tailwind + Zustand + SWR + Recharts + lucide-react + next-pwa.

## Run
```
npm install
npm run dev
```

## What changed vs the old static HTML
- Only the implementation language/framework. No visual, copy, layout, or feature changes.
- `zeno-ai-landing-page__1_.html` -> `app/(marketing)/page.tsx` (route `/`)
- `zeno-ai-app.html` tabs -> real Next.js routes under `app/(app)/`: `/today`, `/roadmap`, `/dashboard`, `/chat`
  (per Frontend Spec §4 Routing Map — clicking a rail tab now navigates instead of a JS class-toggle, same look)
- Both original `<style>` blocks were copied verbatim into `styles/landing.css` and `styles/app-shell.css`,
  each scoped to its own route group so nothing bleeds between pages (they intentionally have different
  base font-size etc.).
- Login-gate + guest button + intake links -> `/today` (was `zeno-ai-app.html`)
- Scroll-reveal (IntersectionObserver) and login-gate JS -> React hooks, same behavior.
- `lib/store.ts` + `lib/store-provider.tsx`: the Zustand store shape and the per-request/SSR-safe
  Context Provider pattern specified in Frontend Spec §5.1/§5.2. Wired into `app/(app)/layout.tsx`.
  Not yet consumed by any page (original HTML had no live state), ready for the real API wiring.
- `lib/api.ts`: typed fetch wrapper stub matching the API Contract in Frontend Spec §6. Set
  `NEXT_PUBLIC_API_BASE_URL` in `.env.local` when the FastAPI backend is up.
- `public/manifest.json`: PWA shell per PRD §2.1.

## Still needed before this is "real"
- Wire `today`/`roadmap`/`dashboard`/`chat` pages to the actual `/tasks/today`, `/roadmap`,
  `/dashboard/{id}`, `/chat/message` endpoints via SWR + `lib/api.ts` (currently static demo markup,
  same numbers as the original HTML mockups).
- `next-pwa` needs real icons in `public/icons/` referenced from `manifest.json`.
- GitHub OAuth client id in `.env.local`.
