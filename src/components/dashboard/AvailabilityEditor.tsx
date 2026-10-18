"use client";

import useAppStore from "@/lib/store";
import { BellRing, Clock } from "lucide-react";

const dayOrder = [1, 2, 3, 4, 5, 6, 0]; // Mon..Sun
const dayNames = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

const timeOptions: string[] = [];
for (let h = 6; h <= 22; h++) {
  timeOptions.push(`${String(h).padStart(2, "0")}:00`);
  if (h < 22) timeOptions.push(`${String(h).padStart(2, "0")}:30`);
}

const AvailabilityEditor = () => {
  const { availability, reminders, setDayHours, setReminders, profile, hasHydrated } =
    useAppStore();

  if (!hasHydrated) {
    return <div className="h-64 animate-pulse rounded-2xl bg-gray-200" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Availability</h1>
      <p className="mt-1 text-sm text-slate-500">
        Your weekly working hours ({profile.timezoneLabel}). Slots are generated
        automatically inside these windows.
      </p>

      <div className="mt-6 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {dayOrder.map((weekday) => {
          const hours = availability[weekday];
          return (
            <div
              key={weekday}
              className="flex flex-wrap items-center gap-4 border-b border-gray-100 px-5 py-4 last:border-0"
            >
              <button
                onClick={() =>
                  setDayHours(weekday, { ...hours, enabled: !hours.enabled })
                }
                className={`relative h-6 w-11 rounded-full transition-colors ${
                  hours.enabled ? "bg-indigo-600" : "bg-gray-300"
                }`}
                aria-label={`toggle ${dayNames[weekday]}`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                    hours.enabled ? "left-[22px]" : "left-0.5"
                  }`}
                />
              </button>
              <span
                className={`w-28 text-sm font-medium ${
                  hours.enabled ? "text-slate-900" : "text-slate-400"
                }`}
              >
                {dayNames[weekday]}
              </span>
              {hours.enabled ? (
                <div className="flex items-center gap-2 text-sm">
                  <select
                    value={hours.start}
                    onChange={(e) =>
                      setDayHours(weekday, { ...hours, start: e.target.value })
                    }
                    className="rounded-lg border border-gray-200 px-2 py-1.5 text-sm outline-none focus:border-indigo-500"
                  >
                    {timeOptions
                      .filter((t) => t < hours.end)
                      .map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                  </select>
                  <span className="text-slate-400">→</span>
                  <select
                    value={hours.end}
                    onChange={(e) =>
                      setDayHours(weekday, { ...hours, end: e.target.value })
                    }
                    className="rounded-lg border border-gray-200 px-2 py-1.5 text-sm outline-none focus:border-indigo-500"
                  >
                    {timeOptions
                      .filter((t) => t > hours.start)
                      .map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                  </select>
                </div>
              ) : (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <Clock className="h-3.5 w-3.5" /> Unavailable
                </span>
              )}
            </div>
          );
        })}
      </div>

      <section className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900">
          <BellRing className="h-4 w-4 text-indigo-600" /> Email reminders
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Reduce no-shows — remind your clients before the session.
        </p>
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={reminders.email24h}
              onChange={(e) => setReminders({ email24h: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600"
            />
            24 hours before the appointment
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={reminders.email1h}
              onChange={(e) => setReminders({ email1h: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600"
            />
            1 hour before the appointment
          </label>
        </div>
      </section>
    </div>
  );
};

export default AvailabilityEditor;
