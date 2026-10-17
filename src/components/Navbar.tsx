import Image from "next/image";
import Link from "next/link";
import SearchBar from "./SearchBar";
import { Bell, Home } from "lucide-react";
import ShoppingCartIcon from "./ShoppingCartIcon";

const Navbar = () => {
    return (
        <nav className="flex items-center justify-between px-4 py-2 border-b border-gray-300">
            <Link href="/" className="flex items-center">
                <Image src="/logo.png" alt="Logo" width={36} height={36} className="w-6 h-6 md:w-9 md:h-9" />
                <p className="hidden md:block text-md font-medium tracking-widest">TRENDSTORE</p>
            </Link>

            <div className="flex items-center gap-6">
                <SearchBar />
                <Link href="/" className="ml-4">
                    <Home className="w-4 h-4 text-gray-500"/>
                </Link>
                <Bell className="w-4 h-4 text-gray-500" />
                <ShoppingCartIcon />
                <Link href="/Login">Sign In</Link>
            </div>

        </nav>
    )
}

export default Navbar;