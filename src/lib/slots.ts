import { Availability, Booking, Service } from "./types";

// ---------- date helpers ----------

export const toISODate = (d: Date): string => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};

export const parseISODate = (iso: string): Date => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};

export const addDays = (d: Date, days: number): Date => {
  const next = new Date(d);
  next.setDate(next.getDate() + days);
  return next;
};

/** "Mon, 12 Jun" */
export const formatDate = (iso: string): string =>
  parseISODate(iso).toLocaleDateString("en-US", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

/** "9:00 AM" */
export const formatTime = (hhmm: string): string => {
  const [h, m] = hhmm.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  const hour = h % 12 === 0 ? 12 : h % 12;
  return `${hour}:${String(m).padStart(2, "0")} ${suffix}`;
};

export const formatMoney = (n: number): string =>
  n === 0 ? "Free" : `$${n.toFixed(n % 1 === 0 ? 0 : 2)}`;

// ---------- slot generation ----------

export const minutesOf = (hhmm: string): number => {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

export const hhmmOf = (mins: number): string => {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
};

/**
 * Available start times for a given date & service:
 * working hours for that weekday, minus past times (for today)
 * and minus slots already taken by a non-cancelled booking.
 */
export const generateSlots = (
  dateISO: string,
  availability: Availability,
  service: Service,
  bookings: Booking[]
): string[] => {
  const date = parseISODate(dateISO);
  const hours = availability[date.getDay()];
  if (!hours?.enabled) return [];

  const start = minutesOf(hours.start);
  const end = minutesOf(hours.end);
  const taken = new Set(
    bookings
      .filter((b) => b.status !== "cancelled" && b.date === dateISO)
      .map((b) => b.time)
  );

  const now = new Date();
  const isToday = toISODate(now) === dateISO;
  const nowMins = now.getHours() * 60 + now.getMinutes();

  const slots: string[] = [];
  for (let t = start; t + service.durationMin <= end; t += service.durationMin) {
    if (isToday && t <= nowMins) continue;
    const slot = hhmmOf(t);
    if (!taken.has(slot)) slots.push(slot);
  }
  return slots;
};

export const upcomingBookableDays = (
  availability: Availability,
  count = 21,
  from: Date = new Date()
): Date[] => {
  const days: Date[] = [];
  for (let i = 0; i < 60 && days.length < count; i++) {
    const d = addDays(from, i);
    if (availability[d.getDay()]?.enabled) days.push(d);
  }
  return days;
};
