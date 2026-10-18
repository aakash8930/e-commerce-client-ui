import { z } from "zod";

// ---------- Domain types ----------

export type Service = {
  id: string;
  name: string;
  description: string;
  durationMin: number;
  price: number;
  /** tailwind background class, e.g. "bg-indigo-500" */
  color: string;
};

export type BookingStatus = "confirmed" | "cancelled" | "completed";

export type Booking = {
  id: string;
  serviceId: string;
  /** YYYY-MM-DD */
  date: string;
  /** HH:MM (24h, local time) */
  time: string;
  clientName: string;
  clientEmail: string;
  clientPhone: string;
  notes?: string;
  status: BookingStatus;
  /** ISO timestamp */
  createdAt: string;
};

export type DayHours = {
  enabled: boolean;
  /** HH:MM */
  start: string;
  /** HH:MM */
  end: string;
};

/** Index 0 = Sunday … 6 = Saturday */
export type Availability = DayHours[];

export type Reminders = {
  email24h: boolean;
  email1h: boolean;
};

export type Profile = {
  /** public booking link: /book/<handle> */
  handle: string;
  businessName: string;
  tagline: string;
  timezoneLabel: string;
};

// ---------- Form schemas ----------

export const bookingFormSchema = z.object({
  clientName: z.string().min(2, "Please enter your name"),
  clientEmail: z.email("Please enter a valid email address"),
  clientPhone: z
    .string()
    .min(7, "Please enter a valid phone number")
    .max(15, "Please enter a valid phone number")
    .regex(/^\+?[\d\s-]+$/, "Please enter a valid phone number"),
  notes: z.string().max(500).optional(),
});

export type BookingFormInputs = z.infer<typeof bookingFormSchema>;

export const serviceFormSchema = z.object({
  name: z.string().min(2, "Service name is required"),
  description: z.string().min(4, "Add a short description"),
  durationMin: z.coerce.number().int().min(15, "Minimum 15 minutes").max(240),
  price: z.coerce.number().min(0, "Price cannot be negative"),
  color: z.string().min(1),
});

export type ServiceFormInputs = z.infer<typeof serviceFormSchema>;

/** Form values before zod coercion (numbers arrive as strings/unknown from inputs) */
export type ServiceFormInput = z.input<typeof serviceFormSchema>;
