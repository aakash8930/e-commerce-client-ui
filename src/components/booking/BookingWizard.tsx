"use client";

import useAppStore from "@/lib/store";
import {
  formatMoney,
  formatTime,
  formatDate,
  generateSlots,
  upcomingBookableDays,
} from "@/lib/slots";
import { Booking, BookingFormInputs, bookingFormSchema } from "@/lib/types";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Globe,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";

const steps = ["Service", "Date & time", "Your details"];

const Skeleton = () => (
  <div className="mx-auto max-w-5xl animate-pulse px-4 py-12">
    <div className="h-24 rounded-2xl bg-gray-100" />
    <div className="mt-6 h-64 rounded-2xl bg-gray-100" />
  </div>
);

const BookingWizard = ({ handle }: { handle: string }) => {
  const {
    profile,
    services,
    availability,
    bookings,
    addBooking,
    hasHydrated,
  } = useAppStore();

  const [step, setStep] = useState(0);
  const [serviceId, setServiceId] = useState<string | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [time, setTime] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState<Booking | null>(null);

  const service = services.find((s) => s.id === serviceId) || null;

  const bookableDays = useMemo(
    () => upcomingBookableDays(availability, 21),
    [availability]
  );

  const slots = useMemo(() => {
    if (!service || !date) return [];
    return generateSlots(date, availability, service, bookings);
  }, [service, date, availability, bookings]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<BookingFormInputs>({
    resolver: zodResolver(bookingFormSchema),
  });

  if (!hasHydrated) return <Skeleton />;

  if (handle !== profile.handle) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-slate-900">
            Booking page not found
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            There is no booking page at{" "}
            <span className="font-medium text-slate-900">/book/{handle}</span>.
          </p>
          <a
            href={`/book/${profile.handle}`}
            className="mt-6 inline-block rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Go to the demo page
          </a>
        </div>
      </main>
    );
  }

  const onSubmit = (data: BookingFormInputs) => {
    if (!service || !date || !time) return;
    const booking = addBooking(service.id, date, time, data);
    setConfirmed(booking);
    setStep(3);
    toast.success("Booking confirmed!");
  };

  const resetWizard = () => {
    setConfirmed(null);
    setServiceId(null);
    setDate(null);
    setTime(null);
    setStep(0);
    reset();
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-6 sm:px-6">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-xl font-bold text-white">
            {profile.businessName.charAt(0)}
          </span>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              {profile.businessName}
            </h1>
            <p className="text-sm text-slate-500">{profile.tagline}</p>
          </div>
          <p className="ml-auto hidden items-center gap-1.5 text-xs text-slate-400 sm:flex">
            <Globe className="h-3.5 w-3.5" />
            {profile.timezoneLabel}
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        {/* step bar */}
        {step < 3 && (
          <ol className="flex items-center gap-2 pb-6 text-sm">
            {steps.map((label, i) => (
              <li key={label} className="flex items-center gap-2">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                    i === step
                      ? "bg-indigo-600 text-white"
                      : i < step
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-gray-200 text-slate-500"
                  }`}
                >
                  {i < step ? "✓" : i + 1}
                </span>
                <span
                  className={
                    i === step ? "font-medium text-slate-900" : "text-slate-500"
                  }
                >
                  {label}
                </span>
                {i < steps.length - 1 && (
                  <span className="mx-1 h-px w-8 bg-gray-300" />
                )}
              </li>
            ))}
          </ol>
        )}

        <div className="grid items-start gap-6 lg:grid-cols-[1fr_320px]">
          {/* main card */}
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
            {step === 0 && (
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Choose a service
                </h2>
                <div className="mt-4 flex flex-col gap-3">
                  {services.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => {
                        setServiceId(s.id);
                        setTime(null);
                      }}
                      className={`flex items-start gap-4 rounded-xl border p-4 text-left transition-colors ${
                        serviceId === s.id
                          ? "border-indigo-600 bg-indigo-50/50"
                          : "border-gray-200 hover:border-slate-300"
                      }`}
                    >
                      <span
                        className={`mt-1 h-3 w-3 shrink-0 rounded-full ${s.color}`}
                      />
                      <span className="flex-1">
                        <span className="flex items-center justify-between">
                          <span className="font-medium text-slate-900">
                            {s.name}
                          </span>
                          <span className="text-sm font-semibold text-slate-900">
                            {formatMoney(s.price)}
                          </span>
                        </span>
                        <span className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                          <Clock className="h-3 w-3" /> {s.durationMin} min
                        </span>
                        <span className="mt-1 block text-sm text-slate-600">
                          {s.description}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
                <button
                  disabled={!service}
                  onClick={() => setStep(1)}
                  className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Continue <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            )}

            {step === 1 && (
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Pick a date & time
                </h2>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
                  <Calendar className="h-4 w-4" /> Next available days
                </p>
                <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
                  {bookableDays.map((d) => {
                    const iso = `${d.getFullYear()}-${String(
                      d.getMonth() + 1
                    ).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
                    const selected = date === iso;
                    return (
                      <button
                        key={iso}
                        onClick={() => {
                          setDate(iso);
                          setTime(null);
                        }}
                        className={`flex min-w-[4.25rem] flex-col items-center rounded-xl border px-3 py-2 ${
                          selected
                            ? "border-indigo-600 bg-indigo-600 text-white"
                            : "border-gray-200 text-slate-600 hover:border-slate-300"
                        }`}
                      >
                        <span className="text-xs opacity-80">
                          {d.toLocaleDateString("en-US", { weekday: "short" })}
                        </span>
                        <span className="text-base font-semibold">
                          {d.getDate()}
                        </span>
                        <span className="text-[10px] opacity-80">
                          {d.toLocaleDateString("en-US", { month: "short" })}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {date && (
                  <>
                    <p className="mt-6 text-sm font-medium text-slate-700">
                      Available times for {formatDate(date)}
                    </p>
                    {slots.length === 0 ? (
                      <p className="mt-3 rounded-xl bg-gray-50 p-4 text-sm text-slate-500">
                        No open slots left on this day — try another date.
                      </p>
                    ) : (
                      <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
                        {slots.map((slot) => (
                          <button
                            key={slot}
                            onClick={() => setTime(slot)}
                            className={`rounded-lg border py-2 text-sm font-medium transition-colors ${
                              time === slot
                                ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                                : "border-gray-200 text-slate-600 hover:border-slate-300"
                            }`}
                          >
                            {formatTime(slot)}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setStep(0)}
                    className="flex items-center gap-2 rounded-xl border border-gray-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:border-slate-400"
                  >
                    <ArrowLeft className="h-4 w-4" /> Back
                  </button>
                  <button
                    disabled={!date || !time}
                    onClick={() => setStep(2)}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    Continue <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {step === 2 && (
              <form onSubmit={handleSubmit(onSubmit)}>
                <h2 className="text-lg font-semibold text-slate-900">
                  Your details
                </h2>
                <div className="mt-4 flex flex-col gap-4">
                  <div className="flex flex-col gap-1">
                    <label htmlFor="clientName" className="text-xs font-medium text-slate-500">
                      Full name
                    </label>
                    <input
                      id="clientName"
                      placeholder="Priya Sharma"
                      className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      {...register("clientName")}
                    />
                    {errors.clientName && (
                      <p className="text-xs text-red-500">
                        {errors.clientName.message}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1">
                    <label htmlFor="clientEmail" className="text-xs font-medium text-slate-500">
                      Email
                    </label>
                    <input
                      id="clientEmail"
                      placeholder="you@example.com"
                      className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      {...register("clientEmail")}
                    />
                    {errors.clientEmail && (
                      <p className="text-xs text-red-500">
                        {errors.clientEmail.message}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1">
                    <label htmlFor="clientPhone" className="text-xs font-medium text-slate-500">
                      Phone
                    </label>
                    <input
                      id="clientPhone"
                      placeholder="+91 98765 43210"
                      className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      {...register("clientPhone")}
                    />
                    {errors.clientPhone && (
                      <p className="text-xs text-red-500">
                        {errors.clientPhone.message}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1">
                    <label htmlFor="notes" className="text-xs font-medium text-slate-500">
                      Anything to prepare? (optional)
                    </label>
                    <textarea
                      id="notes"
                      rows={3}
                      placeholder="Tell them what you'd like to discuss…"
                      className="rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      {...register("notes")}
                    />
                  </div>
                </div>
                <div className="mt-6 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex items-center gap-2 rounded-xl border border-gray-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:border-slate-400"
                  >
                    <ArrowLeft className="h-4 w-4" /> Back
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-300"
                  >
                    Confirm booking
                  </button>
                </div>
              </form>
            )}

            {step === 3 && confirmed && (
              <div className="py-6 text-center">
                <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                  <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                </span>
                <h2 className="mt-4 text-2xl font-semibold text-slate-900">
                  You&apos;re booked!
                </h2>
                <p className="mt-2 text-sm text-slate-600">
                  A confirmation has been sent to{" "}
                  <span className="font-medium text-slate-900">
                    {confirmed.clientEmail}
                  </span>
                  .
                </p>
                <div className="mx-auto mt-6 max-w-sm rounded-xl border border-gray-200 bg-gray-50 p-4 text-left text-sm">
                  <p className="font-medium text-slate-900">
                    {services.find((s) => s.id === confirmed.serviceId)?.name}
                  </p>
                  <p className="mt-1 text-slate-600">
                    {formatDate(confirmed.date)} ·{" "}
                    {formatTime(confirmed.time)}
                  </p>
                </div>
                <button
                  onClick={resetWizard}
                  className="mt-6 rounded-xl border border-gray-300 px-6 py-2.5 text-sm font-medium text-slate-700 hover:border-slate-400"
                >
                  Book another appointment
                </button>
              </div>
            )}
          </div>

          {/* summary */}
          {step < 3 && (
            <aside className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm lg:sticky lg:top-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                Booking summary
              </h3>
              <dl className="mt-4 flex flex-col gap-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Service</dt>
                  <dd className="text-right font-medium text-slate-900">
                    {service?.name || "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Duration</dt>
                  <dd className="text-right font-medium text-slate-900">
                    {service ? `${service.durationMin} min` : "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Date</dt>
                  <dd className="text-right font-medium text-slate-900">
                    {date ? formatDate(date) : "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Time</dt>
                  <dd className="text-right font-medium text-slate-900">
                    {time ? formatTime(time) : "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-gray-100 pt-3">
                  <dt className="text-slate-500">Total</dt>
                  <dd className="text-right text-base font-semibold text-slate-900">
                    {service ? formatMoney(service.price) : "—"}
                  </dd>
                </div>
              </dl>
              <p className="mt-6 text-xs text-slate-400">
                Powered by <span className="font-semibold">Slotly</span>
              </p>
            </aside>
          )}
        </div>
      </div>
    </main>
  );
};

export default BookingWizard;
