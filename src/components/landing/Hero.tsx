import { CalendarCheck, Clock, Star } from "lucide-react";
import Link from "next/link";

const mockSlots = [
  { time: "9:00 AM", state: "open" },
  { time: "9:30 AM", state: "open" },
  { time: "10:00 AM", state: "selected" },
  { time: "10:30 AM", state: "taken" },
  { time: "11:00 AM", state: "open" },
  { time: "11:30 AM", state: "open" },
];

const mockDays = [
  { day: "Mon", date: "12", state: "open" },
  { day: "Tue", date: "13", state: "selected" },
  { day: "Wed", date: "14", state: "open" },
  { day: "Thu", date: "15", state: "open" },
  { day: "Fri", date: "16", state: "open" },
];

const BookingMock = () => {
  return (
    <div className="relative">
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-tr from-indigo-100 via-white to-emerald-100" />
      <div className="relative rounded-2xl border border-gray-200 bg-white p-5 shadow-xl shadow-indigo-100">
        <div className="flex items-center gap-3 border-b border-gray-100 pb-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <CalendarCheck className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold">Strategy Call</p>
            <p className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="h-3 w-3" /> 30 min · Free
            </p>
          </div>
          <span className="ml-auto rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
            Available
          </span>
        </div>

        <p className="pb-2 pt-4 text-xs font-medium uppercase tracking-wide text-slate-400">
          Select a day
        </p>
        <div className="flex gap-2">
          {mockDays.map((d) => (
            <div
              key={d.date}
              className={`flex flex-col items-center rounded-xl border px-3 py-2 text-xs ${
                d.state === "selected"
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : "border-gray-200 text-slate-600"
              }`}
            >
              <span className="opacity-70">{d.day}</span>
              <span className="text-sm font-semibold">{d.date}</span>
            </div>
          ))}
        </div>

        <p className="pb-2 pt-4 text-xs font-medium uppercase tracking-wide text-slate-400">
          Select a time
        </p>
        <div className="grid grid-cols-3 gap-2">
          {mockSlots.map((s) => (
            <div
              key={s.time}
              className={`rounded-lg border py-2 text-center text-xs font-medium ${
                s.state === "selected"
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : s.state === "taken"
                  ? "border-gray-100 text-slate-300 line-through"
                  : "border-gray-200 text-slate-600"
              }`}
            >
              {s.time}
            </div>
          ))}
        </div>

        <button className="mt-4 w-full rounded-xl bg-indigo-600 py-2.5 text-sm font-medium text-white shadow-sm">
          Confirm booking
        </button>
      </div>

      <div className="absolute -bottom-5 -left-5 hidden rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-lg sm:block">
        <p className="flex items-center gap-1 text-xs font-semibold text-slate-900">
          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" /> New booking!
        </p>
        <p className="text-xs text-slate-500">Priya booked 10:00 AM</p>
      </div>
    </div>
  );
};

const Hero = () => {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(60rem_40rem_at_50%_-10rem,rgba(99,102,241,0.12),transparent)]" />
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
            The booking system for service businesses
          </p>
          <h1 className="mt-6 text-4xl font-bold leading-tight tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Get booked.
            <br />
            <span className="text-indigo-600">Without the back-and-forth.</span>
          </h1>
          <p className="mt-6 max-w-lg text-lg text-slate-600">
            Slotly gives you a beautiful booking page, smart availability, and
            automatic reminders. Share one link — clients pick a slot and you
            show up.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition-colors hover:bg-indigo-700"
            >
              Start free — open dashboard
            </Link>
            <Link
              href="/book/slotly-demo"
              className="rounded-xl border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-400"
            >
              Try the live demo →
            </Link>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            No credit card required · Free plan forever · Set up in 2 minutes
          </p>
        </div>

        <BookingMock />
      </div>
    </section>
  );
};

export default Hero;
