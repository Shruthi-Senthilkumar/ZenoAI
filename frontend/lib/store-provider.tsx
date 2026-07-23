"use client";

import { createContext, useContext, useRef } from "react";
import { useStore as useZustandStore } from "zustand";
import {
  createStudentStore,
  type StudentStore,
  type StudentStoreApi,
} from "./store";

const StoreContext = createContext<StudentStoreApi | null>(null);

export function StudentStoreProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const storeRef = useRef<StudentStoreApi>();
  if (!storeRef.current) {
    storeRef.current = createStudentStore(); // one instance per mount, browser-only
  }
  return (
    <StoreContext.Provider value={storeRef.current}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStudentStore<T>(selector: (s: StudentStore) => T): T {
  const store = useContext(StoreContext);
  if (!store) {
    throw new Error(
      "useStudentStore must be used inside StudentStoreProvider"
    );
  }
  return useZustandStore(store, selector);
}
