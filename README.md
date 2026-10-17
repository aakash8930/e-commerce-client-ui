# Trendstore — E-commerce Client UI

A small e-commerce storefront built with Next.js 15 (App Router), React 19, Tailwind CSS v4, Zustand, and react-hook-form + Zod.

## Getting Started

Install dependencies with [pnpm](https://pnpm.io) (this repo uses `pnpm-lock.yaml`):

```bash
pnpm install
```

Run the development server:

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Scripts

```bash
pnpm dev    # start the dev server (turbopack)
pnpm build  # production build
pnpm start  # serve the production build
pnpm lint   # run ESLint
```

## Notes

- Product data is currently hard-coded mock data in `src/components/ProductList.tsx`.
- The cart is persisted in the browser via Zustand (`src/stores/cartStore.ts`).
- Checkout is a UI-only flow — the payment step does not process real payments.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs) — features and API of Next.js
- [Learn Next.js](https://nextjs.org/learn) — interactive Next.js tutorial
- [Tailwind CSS v4](https://tailwindcss.com/docs) — styling
- [Zustand](https://zustand.docs.pmnd.rs/) — state management
