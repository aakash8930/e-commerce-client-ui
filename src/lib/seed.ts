import { addDays, toISODate } from "./slots";
import {
  Availability,
  Booking,
  Profile,
  Reminders,
  Service,
} from "./types";

export const SERVICE_COLORS = [
  "bg-indigo-500",
  "bg-emerald-500",
  "bg-amber-500",
  "bg-rose-500",
  "bg-sky-500",
  "bg-violet-500",
];

export const seedProfile: Profile = {
  handle: "slotly-demo",
  businessName: "Slotly Demo Studio",
  tagline: "Strategy calls & coaching sessions",
  timezoneLabel: "Asia/Kolkata",
};

export const seedServices: Service[] = [
  {
    id: "svc-strategy",
    name: "Strategy Call",
    description:
      "A focused 30-minute call to review your goals and map out next steps.",
    durationMin: 30,
    price: 0,
    color: "bg-indigo-500",
  },
  {
    id: "svc-deepdive",
    name: "Deep-Dive Session",
    description:
      "A full hour of hands-on consulting with an action plan at the end.",
    durationMin: 60,
    price: 79,
    color: "bg-emerald-500",
  },
  {
    id: "svc-checkin",
    name: "Quick Check-in",
    description: "A short 15-minute follow-up to keep your momentum going.",
    durationMin: 15,
    price: 25,
    color: "bg-amber-500",
  },
];

/** Index 0 = Sunday … 6 = Saturday */
export const seedAvailability: Availability = [
  { enabled: false, start: "09:00", end: "17:00" }, // Sun
  { enabled: true, start: "09:00", end: "17:00" }, // Mon
  { enabled: true, start: "09:00", end: "17:00" }, // Tue
  { enabled: true, start: "09:00", end: "17:00" }, // Wed
  { enabled: true, start: "09:00", end: "17:00" }, // Thu
  { enabled: true, start: "09:00", end: "16:00" }, // Fri
  { enabled: true, start: "10:00", end: "14:00" }, // Sat
];

export const seedReminders: Reminders = {
  email24h: true,
  email1h: false,
};

export const seedBookings: Booking[] = (() => {
  const now = new Date().toISOString();
  const day = (offset: number) => toISODate(addDays(new Date(), offset));
  return [
    {
      id: "bk-1",
      serviceId: "svc-deepdive",
      date: day(1),
      time: "10:00",
      clientName: "Priya Sharma",
      clientEmail: "priya@example.com",
      clientPhone: "+91 98765 43210",
      notes: "Want to review my launch plan.",
      status: "confirmed",
      createdAt: now,
    },
    {
      id: "bk-2",
      serviceId: "svc-strategy",
      date: day(1),
      time: "14:00",
      clientName: "Rahul Verma",
      clientEmail: "rahul@example.com",
      clientPhone: "+91 98111 22334",
      status: "confirmed",
      createdAt: now,
    },
    {
      id: "bk-3",
      serviceId: "svc-checkin",
      date: day(2),
      time: "11:00",
      clientName: "Meera Iyer",
      clientEmail: "meera@example.com",
      clientPhone: "+91 99000 11223",
      status: "confirmed",
      createdAt: now,
    },
    {
      id: "bk-4",
      serviceId: "svc-deepdive",
      date: day(-2),
      time: "15:00",
      clientName: "Arjun Patel",
      clientEmail: "arjun@example.com",
      clientPhone: "+91 97000 55667",
      status: "completed",
      createdAt: now,
    },
    {
      id: "bk-5",
      serviceId: "svc-strategy",
      date: day(-5),
      time: "09:00",
      clientName: "Sara Khan",
      clientEmail: "sara@example.com",
      clientPhone: "+91 96000 88990",
      status: "cancelled",
      createdAt: now,
    },
  ];
})();
