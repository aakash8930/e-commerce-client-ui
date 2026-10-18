import Link from "next/link";
import Logo from "../Logo";

const LandingFooter = () => {
  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-8 px-4 py-12 sm:px-6 md:flex-row">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3 text-sm leading-relaxed text-slate-500">
            The appointment booking system for coaches, tutors, salons and
            consultants. Share your link, get booked, get paid.
          </p>
          <p className="mt-4 text-xs text-slate-400">
            Demo build — bookings are stored in your browser only.
          </p>
        </div>
        <div className="flex gap-16 text-sm">
          <div className="flex flex-col gap-3">
            <p className="font-semibold text-slate-900">Product</p>
            <Link href="#features" className="text-slate-500 hover:text-slate-900">
              Features
            </Link>
            <Link href="#pricing" className="text-slate-500 hover:text-slate-900">
              Pricing
            </Link>
            <Link href="/book/slotly-demo" className="text-slate-500 hover:text-slate-900">
              Live demo
            </Link>
          </div>
          <div className="flex flex-col gap-3">
            <p className="font-semibold text-slate-900">Company</p>
            <Link href="#" className="text-slate-500 hover:text-slate-900">
              About
            </Link>
            <Link href="#" className="text-slate-500 hover:text-slate-900">
              Contact
            </Link>
            <Link href="#" className="text-slate-500 hover:text-slate-900">
              Terms & Privacy
            </Link>
          </div>
        </div>
      </div>
      <div className="border-t border-gray-200 py-6 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} Slotly. All rights reserved.
      </div>
    </footer>
  );
};

export default LandingFooter;
