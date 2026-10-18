"use client";

import useAppStore from "@/lib/store";
import {
  formatMoney,
  formatTime,
  formatDate,
  toISODate,
} from "@/lib/slots";
import { Booking } from "@/lib/types";
import {
  CalendarDays,
  CheckCircle2,
  Clock,
  Copy,
  DollarSign,
  Scissors,
} from "lucide-react";
import Link from "next/link";
import { toast } from "react-toastify";

const StatCard = ({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  hint: string;
}) => (
  <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <Icon className="h-4 w-4" />
      {label}
    </div>
    <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    <p className="mt-1 text-xs text-slate-400">{hint}</p>
  </div>
);

const BookingRow = ({ booking }: { booking: Booking }) => {
  const service = useAppStore((s) =>
    s.services.find((x) => x.id === booking.serviceId)
  );
  return (
    <div className="flex items-center gap-3 border-b border-gray-100 py-3 last:border-0">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-slate-600">
        {booking.clientName
          .split(" ")
          .map((w) => w.charAt(0))
          .slice(0, 2)
          .join("")}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">
          {booking.clientName}
        </p>
        <p className="truncate text-xs text-slate-500">
          {service?.name || "Service"} · {formatDate(booking.date)} at{" "}
          {formatTime(booking.time)}
        </p>
      </div>
      <span className="text-sm font-semibold text-slate-900">
        {service ? formatMoney(service.price) : "—"}
      </span>
    </div>
  );
};

const DashboardPage = () => {
  const { bookings, services, profile, hasHydrated } = useAppStore();

  if (!hasHydrated) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 w-56 rounded-lg bg-gray-200" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-gray-200" />
          ))}
        </div>
      </div>
    );
  }

  const today = toISODate(new Date());
  const now = new Date();
  const weekEnd = new Date();
  weekEnd.setDate(now.getDate() + 7);

  const active = bookings.filter((b) => b.status !== "cancelled");
  const upcoming = active
    .filter(
      (b) => b.date > today || (b.date === today && b.time >= "00:00")
    )
    .filter((b) => b.status === "confirmed")
    .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
  const thisWeek = active.filter((b) => {
    const d = new Date(`${b.date}T00:00:00`);
    return d >= new Date(`${today}T00:00:00`) && d <= weekEnd;
  });
  const thisMonth = active.filter((b) => b.date.slice(0, 7) === today.slice(0, 7));
  const revenue = thisMonth.reduce((acc, b) => {
    const svc = services.find((s) => s.id === b.serviceId);
    return acc + (svc?.price || 0);
  }, 0);

  const todayBookings = upcoming.filter((b) => b.date === today);
  const bookingUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/book/${profile.handle}`
      : `/book/${profile.handle}`;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(bookingUrl);
      toast.success("Booking link copied!");
    } catch {
      toast.info("Copy failed — select the link manually");
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Overview</h1>
          <p className="mt-1 text-sm text-slate-500">
            Here&apos;s what&apos;s happening at {profile.businessName}.
          </p>
        </div>
        <Link
          href="/dashboard/bookings"
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Manage bookings
        </Link>
      </div>

      {/* stats */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={CalendarDays}
          label="Upcoming"
          value={String(upcoming.length)}
          hint="confirmed bookings ahead"
        />
        <StatCard
          icon={Clock}
          label="This week"
          value={String(thisWeek.length)}
          hint="bookings in the next 7 days"
        />
        <StatCard
          icon={DollarSign}
          label="Revenue (month)"
          value={formatMoney(revenue)}
          hint="from non-cancelled bookings"
        />
        <StatCard
          icon={Scissors}
          label="Active services"
          value={String(services.length)}
          hint="bookable right now"
        />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* today */}
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Today&apos;s schedule
          </h2>
          {todayBookings.length === 0 ? (
            <p className="mt-4 rounded-xl bg-gray-50 p-4 text-sm text-slate-500">
              Nothing booked today — enjoy the calm, or share your booking link.
            </p>
          ) : (
            <div className="mt-2">
              {todayBookings.map((b) => (
                <BookingRow key={b.id} booking={b} />
              ))}
            </div>
          )}
        </section>

        {/* booking link */}
        <section className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-6">
          <h2 className="text-base font-semibold text-slate-900">
            Your booking link
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Share it anywhere — clients can book you 24/7.
          </p>
          <div className="mt-4 flex items-center gap-2">
            <input
              readOnly
              value={bookingUrl}
              onFocus={(e) => e.currentTarget.select()}
              className="min-w-0 flex-1 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none"
            />
            <button
              onClick={copyLink}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Copy className="h-3.5 w-3.5" /> Copy
            </button>
          </div>
          <Link
            href={`/book/${profile.handle}`}
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            Open booking page →
          </Link>
        </section>
      </div>

      {/* recent */}
      <section className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">
            Upcoming appointments
          </h2>
          <Link
            href="/dashboard/bookings"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            View all
          </Link>
        </div>
        {upcoming.length === 0 ? (
          <p className="mt-4 flex items-center gap-2 rounded-xl bg-gray-50 p-4 text-sm text-slate-500">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            You&apos;re all caught up.
          </p>
        ) : (
          <div className="mt-2">
            {upcoming.slice(0, 5).map((b) => (
              <BookingRow key={b.id} booking={b} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
