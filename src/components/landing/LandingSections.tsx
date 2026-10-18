import {
  ArrowRight,
  BarChart3,
  BellRing,
  CalendarClock,
  CreditCard,
  Globe,
  Users,
} from "lucide-react";
import Link from "next/link";

const features = [
  {
    icon: Globe,
    title: "Public booking page",
    text: "A clean, shareable page at slotly.app/your-name where clients book you 24/7.",
  },
  {
    icon: CalendarClock,
    title: "Smart availability",
    text: "Set working hours per weekday. Slots are generated around your real calendar.",
  },
  {
    icon: BellRing,
    title: "Automated reminders",
    text: "Email reminders 24 hours and 1 hour before, so no-shows drop dramatically.",
  },
  {
    icon: Users,
    title: "Client directory",
    text: "Every booking is filed under a client — visits, spend and history at a glance.",
  },
  {
    icon: BarChart3,
    title: "Business insights",
    text: "See upcoming bookings, weekly load and revenue in one simple dashboard.",
  },
  {
    icon: CreditCard,
    title: "Payments-ready",
    text: "Charge for sessions up front. Connect Stripe or Razorpay when you go live.",
  },
];

const steps = [
  {
    n: "1",
    title: "Create your page",
    text: "Add your services, prices and working hours. Your booking page is ready instantly.",
  },
  {
    n: "2",
    title: "Share your link",
    text: "Put it in your bio, website or Instagram. Clients see live availability.",
  },
  {
    n: "3",
    title: "Get booked",
    text: "You both get confirmations and reminders. Your calendar fills itself.",
  },
];

const tiers = [
  {
    name: "Starter",
    price: "$0",
    cadence: "forever",
    text: "For trying things out",
    items: ["1 service", "Up to 20 bookings/mo", "Booking page", "Email reminders"],
    cta: "Start free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$12",
    cadence: "per month",
    text: "For working professionals",
    items: [
      "Unlimited services",
      "Unlimited bookings",
      "Reminders + insights",
      "Client directory",
      "Payments-ready",
    ],
    cta: "Start 14-day trial",
    highlight: true,
  },
  {
    name: "Business",
    price: "$29",
    cadence: "per month",
    text: "For teams & studios",
    items: [
      "Everything in Pro",
      "Up to 10 team members",
      "Custom domain",
      "API access",
      "Priority support",
    ],
    cta: "Start 14-day trial",
    highlight: false,
  },
];

const LandingSections = () => {
  return (
    <>
      {/* social proof */}
      <section className="border-y border-gray-100 bg-gray-50">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-10 gap-y-4 px-4 py-8 sm:px-6">
          <p className="text-sm text-slate-500">
            Trusted by 2,400+ coaches, tutors, stylists and consultants
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            <span>GrowWithMe</span>
            <span>Studio&nbsp;Nine</span>
            <span>ClarityCounsel</span>
            <span>SalonAdda</span>
            <span>TutorBase</span>
          </div>
        </div>
      </section>

      {/* features */}
      <section id="features" className="scroll-mt-16">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
              Features
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Everything you need to run your bookings
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              No more WhatsApp threads, spreadsheets or double bookings.
            </p>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-slate-900">
                  {f.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {f.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* how it works */}
      <section id="how-it-works" className="scroll-mt-16 bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-indigo-400">
              How it works
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Live in three steps
            </h2>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((s) => (
              <div
                key={s.n}
                className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">
                  {s.n}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-white">
                  {s.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">
                  {s.text}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-slate-900 transition-colors hover:bg-slate-100"
            >
              Set up my page <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* pricing */}
      <section id="pricing" className="scroll-mt-16">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
              Pricing
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Simple pricing that pays for itself
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              One saved no-show covers a month of Pro.
            </p>
          </div>
          <div className="mt-12 grid gap-6 lg:grid-cols-3">
            {tiers.map((t) => (
              <div
                key={t.name}
                className={`relative flex flex-col rounded-2xl border bg-white p-8 ${
                  t.highlight
                    ? "border-indigo-600 shadow-xl shadow-indigo-100"
                    : "border-gray-200 shadow-sm"
                }`}
              >
                {t.highlight && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white">
                    Most popular
                  </span>
                )}
                <h3 className="text-lg font-semibold text-slate-900">
                  {t.name}
                </h3>
                <p className="mt-1 text-sm text-slate-500">{t.text}</p>
                <p className="mt-6 flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-slate-900">
                    {t.price}
                  </span>
                  <span className="text-sm text-slate-500">{t.cadence}</span>
                </p>
                <ul className="mt-6 flex flex-col gap-3 text-sm text-slate-600">
                  {t.items.map((i) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                        ✓
                      </span>
                      {i}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/dashboard"
                  className={`mt-8 rounded-xl px-4 py-2.5 text-center text-sm font-semibold transition-colors ${
                    t.highlight
                      ? "bg-indigo-600 text-white hover:bg-indigo-700"
                      : "border border-gray-300 text-slate-700 hover:border-slate-400"
                  }`}
                >
                  {t.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
};

export default LandingSections;
