import { CalendarCheck } from "lucide-react";
import Link from "next/link";

const Logo = ({
  href = "/",
  light = false,
}: {
  href?: string;
  light?: boolean;
}) => {
  return (
    <Link href={href} className="flex items-center gap-2">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
        <CalendarCheck className="h-4 w-4" />
      </span>
      <span
        className={`text-lg font-semibold tracking-tight ${
          light ? "text-white" : "text-slate-900"
        }`}
      >
        Slotly
      </span>
    </Link>
  );
};

export default Logo;
