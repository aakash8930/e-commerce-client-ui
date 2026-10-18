import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import {
  seedAvailability,
  seedBookings,
  seedProfile,
  seedReminders,
  seedServices,
} from "./seed";
import {
  Availability,
  Booking,
  BookingFormInputs,
  Profile,
  Reminders,
  Service,
  ServiceFormInputs,
} from "./types";

export type AppState = {
  profile: Profile;
  services: Service[];
  availability: Availability;
  reminders: Reminders;
  bookings: Booking[];
  hasHydrated: boolean;
};

export type AppActions = {
  setHasHydrated: (hasHydrated: boolean) => void;
  addService: (data: ServiceFormInputs) => void;
  updateService: (id: string, data: ServiceFormInputs) => void;
  deleteService: (id: string) => void;
  addBooking: (
    serviceId: string,
    date: string,
    time: string,
    client: BookingFormInputs
  ) => Booking;
  cancelBooking: (id: string) => void;
  completeBooking: (id: string) => void;
  setDayHours: (weekday: number, hours: Availability[number]) => void;
  setReminders: (reminders: Partial<Reminders>) => void;
};

export const useAppStore = create<AppState & AppActions>()(
  persist(
    (set) => ({
      profile: seedProfile,
      services: seedServices,
      availability: seedAvailability,
      reminders: seedReminders,
      bookings: seedBookings,
      hasHydrated: false,

      setHasHydrated: (hasHydrated) => set({ hasHydrated }),

      addService: (data) =>
        set((state) => ({
          services: [
            ...state.services,
            { id: crypto.randomUUID(), ...data },
          ],
        })),

      updateService: (id, data) =>
        set((state) => ({
          services: state.services.map((s) =>
            s.id === id ? { ...s, ...data } : s
          ),
        })),

      deleteService: (id) =>
        set((state) => ({
          services: state.services.filter((s) => s.id !== id),
        })),

      addBooking: (serviceId, date, time, client) => {
        const booking: Booking = {
          id: crypto.randomUUID(),
          serviceId,
          date,
          time,
          ...client,
          status: "confirmed",
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ bookings: [...state.bookings, booking] }));
        return booking;
      },

      cancelBooking: (id) =>
        set((state) => ({
          bookings: state.bookings.map((b) =>
            b.id === id ? { ...b, status: "cancelled" as const } : b
          ),
        })),

      completeBooking: (id) =>
        set((state) => ({
          bookings: state.bookings.map((b) =>
            b.id === id ? { ...b, status: "completed" as const } : b
          ),
        })),

      setDayHours: (weekday, hours) =>
        set((state) => {
          const availability = [...state.availability];
          availability[weekday] = hours;
          return { availability };
        }),

      setReminders: (reminders) =>
        set((state) => ({ reminders: { ...state.reminders, ...reminders } })),
    }),
    {
      name: "slotly-store",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

export default useAppStore;
