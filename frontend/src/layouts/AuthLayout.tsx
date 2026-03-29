import { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
      <div className="w-full max-w-md bg-zinc-900 p-8 rounded-2xl shadow-xl border border-zinc-800">
        {children}
      </div>
    </div>
  );
}
