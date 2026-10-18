"use client";

import useAppStore from "@/lib/store";
import {
  CalendarDays,
  Clock,
  ExternalLink,
  LayoutDashboard,
  Scissors,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Logo from "../Logo";

const nav = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/bookings", label: "Bookings", icon: CalendarDays },
  { href: "/dashboard/services", label: "Services", icon: Scissors },
  { href: "/dashboard/availability", label: "Availability", icon: Clock },
  { href: "/dashboard/clients", label: "Clients", icon: Users },
];

const AppShell = ({ children }: { children: React.ReactNode }) => {
  const pathname = usePathname();
  const profile = useAppStore((s) => s.profile);
  const hasHydrated = useAppStore((s) => s.hasHydrated);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* sidebar (desktop) */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-gray-200 bg-white md:flex">
        <div className="p-5">
          <Logo href="/dashboard" />
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {nav.map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-slate-600 hover:bg-gray-50 hover:text-slate-900"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-gray-200 p-4">
          <Link
            href={`/book/${profile.handle}`}
            className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300"
          >
            View booking page
            <ExternalLink className="h-3.5 w-3.5" />
          </Link>
          <p className="mt-3 truncate text-xs text-slate-400">
            {hasHydrated ? profile.businessName : "…"}
          </p>
        </div>
      </aside>

      {/* main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* mobile nav */}
        <div className="sticky top-0 z-40 border-b border-gray-200 bg-white md:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <Logo href="/dashboard" />
            <Link
              href={`/book/${profile.handle}`}
              className="text-xs font-medium text-indigo-600"
            >
              Booking page ↗
            </Link>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-2 pb-2">
            {nav.map((item) => {
              const active =
                item.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium ${
                    active
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-500 hover:bg-gray-50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
