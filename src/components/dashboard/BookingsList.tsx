"use client";

import useAppStore from "@/lib/store";
import { formatDate, formatMoney, formatTime, toISODate } from "@/lib/slots";
import { BookingStatus } from "@/lib/types";
import { Ban, CheckCircle2, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "react-toastify";

type Tab = "upcoming" | "past" | "cancelled";

const statusStyles: Record<BookingStatus, string> = {
  confirmed: "bg-indigo-50 text-indigo-700",
  completed: "bg-emerald-50 text-emerald-700",
  cancelled: "bg-red-50 text-red-600",
};

const BookingsList = () => {
  const { bookings, services, cancelBooking, completeBooking, hasHydrated } =
    useAppStore();
  const [tab, setTab] = useState<Tab>("upcoming");
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    const today = toISODate(new Date());
    const withService = bookings.map((b) => ({
      booking: b,
      service: services.find((s) => s.id === b.serviceId),
    }));

    const filtered = withService.filter(({ booking }) => {
      if (tab === "cancelled") return booking.status === "cancelled";
      if (tab === "past")
        return (
          booking.status === "completed" ||
          (booking.status === "confirmed" && booking.date < today)
        );
      return booking.status === "confirmed" && booking.date >= today;
    });

    const q = query.trim().toLowerCase();
    return filtered
      .filter(({ booking, service }) =>
        q
          ? booking.clientName.toLowerCase().includes(q) ||
            booking.clientEmail.toLowerCase().includes(q) ||
            (service?.name || "").toLowerCase().includes(q)
          : true
      )
      .sort((a, b) =>
        tab === "past"
          ? (b.booking.date + b.booking.time).localeCompare(
              a.booking.date + a.booking.time
            )
          : (a.booking.date + a.booking.time).localeCompare(
              b.booking.date + b.booking.time
            )
      );
  }, [bookings, services, tab, query]);

  if (!hasHydrated) {
    return <div className="h-64 animate-pulse rounded-2xl bg-gray-200" />;
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "upcoming", label: "Upcoming" },
    { id: "past", label: "Past" },
    { id: "cancelled", label: "Cancelled" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Bookings</h1>
      <p className="mt-1 text-sm text-slate-500">
        Every appointment made through your booking page.
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 rounded-xl bg-gray-100 p-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 shadow-sm">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search client or service…"
            className="w-48 text-sm outline-none"
          />
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {rows.length === 0 ? (
          <p className="p-8 text-center text-sm text-slate-500">
            No {tab} bookings{query ? " match your search" : ""}.
          </p>
        ) : (
          rows.map(({ booking, service }) => (
            <div
              key={booking.id}
              className="flex flex-wrap items-center gap-3 border-b border-gray-100 p-4 last:border-0"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-slate-600">
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
                  {booking.clientEmail} · {booking.clientPhone}
                </p>
              </div>
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium text-slate-900">
                  {service?.name || "Service"}
                </p>
                <p className="text-xs text-slate-500">
                  {formatDate(booking.date)} · {formatTime(booking.time)}
                </p>
              </div>
              <div className="w-20 text-right text-sm font-semibold text-slate-900">
                {service ? formatMoney(service.price) : "—"}
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${statusStyles[booking.status]}`}
              >
                {booking.status}
              </span>
              <div className="flex gap-2">
                {booking.status === "confirmed" && booking.date >= toISODate(new Date()) && (
                  <button
                    onClick={() => {
                      cancelBooking(booking.id);
                      toast.success("Booking cancelled");
                    }}
                    className="flex items-center gap-1 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                  >
                    <Ban className="h-3 w-3" /> Cancel
                  </button>
                )}
                {booking.status === "confirmed" && booking.date < toISODate(new Date()) && (
                  <button
                    onClick={() => {
                      completeBooking(booking.id);
                      toast.success("Marked as completed");
                    }}
                    className="flex items-center gap-1 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700"
                  >
                    <CheckCircle2 className="h-3 w-3" /> Complete
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BookingsList;
