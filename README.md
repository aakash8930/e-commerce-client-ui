# Slotly — Appointment Booking SaaS

Slotly is a Calendly-style appointment booking product for service businesses
(coaches, tutors, salons, consultants). It ships as a complete MVP:

- **Marketing site** with hero, features, how-it-works and pricing
- **Public booking page** at `/book/<handle>` — pick service → date → time → done
- **Dashboard** at `/dashboard` — overview stats, bookings, services, weekly
  availability, reminders and a client directory

Built with Next.js 15 (App Router), React 19, Tailwind CSS v4, Zustand,
and react-hook-form + Zod.

> Demo build: all data is stored in the browser (localStorage) — no backend
> required. Swap `src/lib/store.ts` for API calls to make it real.

## Getting Started

Install dependencies with [pnpm](https://pnpm.io):

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

- Marketing site: `/`
- Live demo booking page: `/book/slotly-demo`
- Dashboard: `/dashboard`

## Scripts

```bash
pnpm dev    # dev server (turbopack)
pnpm build  # production build
pnpm start  # serve the production build
pnpm lint   # ESLint
```

## Structure

```
src/
  app/                # routes (landing, /book/[handle], /dashboard/*)
  components/
    landing/          # marketing sections
    booking/          # public booking wizard
    dashboard/        # app shell + management views
  lib/
    store.ts          # Zustand store (persisted to localStorage)
    slots.ts          # date/time + slot generation logic
    seed.ts           # demo profile, services, availability, bookings
    types.ts          # domain types + zod form schemas
```
