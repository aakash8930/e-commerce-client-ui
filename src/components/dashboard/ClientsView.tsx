"use client";

import useAppStore from "@/lib/store";
import { formatDate, formatMoney, toISODate } from "@/lib/slots";
import { Mail, Phone } from "lucide-react";
import { useMemo } from "react";

type ClientRow = {
  email: string;
  name: string;
  phone: string;
  visits: number;
  spend: number;
  lastVisit?: string;
  upcoming: number;
};

const ClientsView = () => {
  const { bookings, services, hasHydrated } = useAppStore();

  const clients = useMemo<ClientRow[]>(() => {
    const map = new Map<string, ClientRow>();
    const today = toISODate(new Date());

    for (const b of bookings) {
      if (b.status === "cancelled") continue;
      const row =
        map.get(b.clientEmail) ||
        ({
          email: b.clientEmail,
          name: b.clientName,
          phone: b.clientPhone,
          visits: 0,
          spend: 0,
          upcoming: 0,
        } as ClientRow);

      const service = services.find((s) => s.id === b.serviceId);
      if (b.date < today) {
        row.visits += 1;
        row.spend += service?.price || 0;
        if (!row.lastVisit || b.date > row.lastVisit) row.lastVisit = b.date;
      } else {
        row.upcoming += 1;
      }
      map.set(b.clientEmail, row);
    }

    return [...map.values()].sort(
      (a, b) => b.visits + b.upcoming - (a.visits + a.upcoming)
    );
  }, [bookings, services]);

  if (!hasHydrated) {
    return <div className="h-64 animate-pulse rounded-2xl bg-gray-200" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Clients</h1>
      <p className="mt-1 text-sm text-slate-500">
        Everyone who has booked you — automatically filed from your bookings.
      </p>

      {clients.length === 0 ? (
        <p className="mt-6 rounded-2xl border border-dashed border-gray-300 p-8 text-center text-sm text-slate-500">
          No clients yet. They&apos;ll appear here after your first booking.
        </p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {clients.map((c) => (
            <div
              key={c.email}
              className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-indigo-50 text-sm font-semibold text-indigo-700">
                  {c.name
                    .split(" ")
                    .map((w) => w.charAt(0))
                    .slice(0, 2)
                    .join("")}
                </span>
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-900">{c.name}</p>
                  <p className="truncate text-xs text-slate-500">{c.email}</p>
                </div>
              </div>
              <div className="mt-4 space-y-1.5 text-xs text-slate-500">
                <p className="flex items-center gap-1.5">
                  <Phone className="h-3 w-3" /> {c.phone}
                </p>
                <p className="flex items-center gap-1.5">
                  <Mail className="h-3 w-3" /> {c.email}
                </p>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 border-t border-gray-100 pt-4 text-center">
                <div>
                  <p className="text-base font-semibold text-slate-900">
                    {c.visits}
                  </p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-400">
                    Visits
                  </p>
                </div>
                <div>
                  <p className="text-base font-semibold text-slate-900">
                    {formatMoney(c.spend)}
                  </p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-400">
                    Spend
                  </p>
                </div>
                <div>
                  <p className="text-base font-semibold text-slate-900">
                    {c.upcoming}
                  </p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-400">
                    Upcoming
                  </p>
                </div>
              </div>
              {c.lastVisit && (
                <p className="mt-3 text-[11px] text-slate-400">
                  Last visit: {formatDate(c.lastVisit)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ClientsView;
