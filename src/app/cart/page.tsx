"use client";

import PaymentForm from "@/components/PaymentForm";
import ShippingForm from "@/components/ShippingForm";
import useCartStore from "@/stores/cartStore";
import { ShippingFormInputs } from "@/types";
import { ArrowRight, Minus, Plus } from "lucide-react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

const steps = [
    {
        id: 1,
        title: "Shopping Cart",
    },
    {
        id: 2,
        title: "Shipping Address",
    },
    {
        id: 3,
        title: "Payment Method",
    },
];

const CartContent = () => {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [shippingForm, setShippingForm] = useState<ShippingFormInputs>();

    const activeStep = parseInt(searchParams.get("step") || "1");

    const { cart, increaseQuantity, decreaseQuantity } = useCartStore();

    return (
        <div className="flex flex-col gap-8 items-center justify-center mt-12">
            {/* TITLE */}
            <h1 className="text-2xl font-medium">Your Shopping Cart</h1>
            {/* STEPS */}
            <div className="flex flex-row lg:flex-row items-center gap-8 lg:gap-16">
                {steps.map((step) => (
                    <div
                        className={`flex items-center gap-2 border-b-2 pb-4 ${step.id === activeStep ? "border-gray-800" : "border-gray-200"
                            }`}
                        key={step.id}
                    >
                        <div
                            className={`w-6 h-6 rounded-full text-white p-4 flex items-center justify-center ${step.id === activeStep ? "bg-gray-800" : "bg-gray-400"
                                }`}
                        >
                            {step.id}
                        </div>
                        <p
                            className={`text-xs lg:text-sm font-medium ${step.id === activeStep ? "text-gray-800" : "text-gray-400"
                                }`}
                        >
                            {step.title}
                        </p>
                    </div>
                ))}
            </div>
            {/* STEPS & DETAILS */}
            <div className="w-full flex flex-col lg:flex-row gap-16">
                {/* STEPS */}
                <div className="w-full lg:w-7/12 shadow-lg border-1 border-gray-100 p-8 rounded-lg flex flex-col gap-8">
                    {activeStep === 1 ? (
                        cart.map((item) => (
                            // SINGLE CART ITEM
                            <div
                                className="flex items-center justify-between"
                                key={item.id + item.selectedSize + item.selectedColor}
                            >
                                {/* IMAGE AND DETAILS */}
                                <div className="flex gap-8">
                                    {/* IMAGE */}
                                    <div className="relative w-32 h-32 bg-gray-50 rounded-lg overflow-hidden">
                                        <Image
                                            src={item.images[item.selectedColor]}
                                            alt={item.name}
                                            fill
                                            className="object-contain"
                                        />
                                    </div>
                                    {/* ITEM DETAILS */}
                                    <div className="flex flex-col justify-between">
                                        <div className="flex flex-col gap-1">
                                            <p className="text-sm font-medium">{item.name}</p>
                                            <p className="text-xs text-gray-500">
                                                Quantity: {item.quantity}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Size: {item.selectedSize}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Color: {item.selectedColor}
                                            </p>
                                        </div>
                                        <p className="font-medium">${item.price.toFixed(2)}</p>
                                    </div>
                                </div>
                                {/* QUANTITY CONTROLS */}
                                <div className="flex items-center gap-2">
                                    <button
                                        className="cursor-pointer border-1 border-gray-300 p-1 rounded-md"
                                        onClick={() => decreaseQuantity(item)}
                                    >
                                        <Minus className="w-4 h-4" />
                                    </button>
                                    <span className="w-4 text-center">{item.quantity}</span>
                                    <button
                                        className="cursor-pointer border-1 border-gray-300 p-1 rounded-md"
                                        onClick={() => increaseQuantity(item)}
                                    >
                                        <Plus className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : activeStep === 2 ? (
                        <ShippingForm setShippingForm={setShippingForm} />
                    ) : activeStep === 3 && shippingForm ? (
                        <PaymentForm />
                    ) : (
                        <div className="flex flex-col items-start gap-4 text-sm text-gray-500">
                            <p>Please complete your shipping address before payment.</p>
                            <button
                                onClick={() => router.push("/cart?step=2", { scroll: false })}
                                className="bg-gray-800 hover:bg-gray-900 transition-all duration-300 text-white px-4 py-2 rounded-lg cursor-pointer"
                            >
                                Go to Shipping Address
                            </button>
                        </div>
                    )}
                </div>
                {/* DETAILS */}
                <div className="w-full lg:w-5/12 shadow-lg border-1 border-gray-100 p-8 rounded-lg flex flex-col gap-8 h-max">
                    <h2 className="font-semibold">Cart Details</h2>
                    <div className="flex flex-col gap-4">
                        <div className="flex justify-between text-sm">
                            <p className="text-gray-500">Subtotal</p>
                            <p className="font-medium">
                                $
                                {cart
                                    .reduce((acc, item) => acc + item.price * item.quantity, 0)
                                    .toFixed(2)}
                            </p>
                        </div>
                        <div className="flex justify-between text-sm">
                            <p className="text-gray-500">Discount(10%)</p>
                            <p className="font-medium">$ 10</p>
                        </div>
                        <div className="flex justify-between text-sm">
                            <p className="text-gray-500">Shipping Fee</p>
                            <p className="font-medium">$10</p>
                        </div>
                        <hr className="border-gray-200" />
                        <div className="flex justify-between">
                            <p className="text-gray-800 font-semibold">Total</p>
                            <p className="font-medium">
                                $
                                {cart
                                    .reduce((acc, item) => acc + item.price * item.quantity, 0)
                                    .toFixed(2)}
                            </p>
                        </div>
                    </div>
                    {activeStep === 1 && (
                        <button
                            onClick={() => router.push("/cart?step=2", { scroll: false })}
                            className="w-full bg-gray-800 hover:bg-gray-900 transition-all duration-300 text-white p-2 rounded-lg cursor-pointer flex items-center justify-center gap-2"
                        >
                            Continue
                            <ArrowRight className="w-3 h-3" />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

const CartPage = () => {
    return (
        <Suspense>
            <CartContent />
        </Suspense>
    );
};

export default CartPage;
