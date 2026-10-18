"use client";

import useAppStore from "@/lib/store";
import { useEffect } from "react";

/** Rehydrates the persisted store after mount (SSR-safe). */
const StoreHydrator = () => {
  useEffect(() => {
    useAppStore.persist.rehydrate();
  }, []);
  return null;
};

export default StoreHydrator;
