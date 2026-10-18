import { Menu } from "lucide-react";
import Link from "next/link";
import Logo from "../Logo";

const LandingNav = () => {
  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Logo />
        <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
          <Link href="#features" className="hover:text-slate-900">
            Features
          </Link>
          <Link href="#how-it-works" className="hover:text-slate-900">
            How it works
          </Link>
          <Link href="#pricing" className="hover:text-slate-900">
            Pricing
          </Link>
          <Link
            href="/book/slotly-demo"
            className="hover:text-slate-900"
          >
            Live demo
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            Open dashboard
          </Link>
          <Menu className="h-5 w-5 text-slate-500 md:hidden" />
        </div>
      </div>
    </header>
  );
};

export default LandingNav;
