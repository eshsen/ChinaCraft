"use client";

import Link from "next/link";

export function Header() {
  return (
    <div className="mb-14 flex items-start justify-between">
      <Link
        href="/"
        aria-label="ChinaCraft"
        className="h-14 w-14 rounded-sm bg-[#b50709] p-2"
      >
        <div className="relative h-full w-full">
          <div className="absolute left-0 top-1 h-0.5 w-7 bg-white" />
          <div className="absolute left-0 top-4 h-0.5 w-7 bg-white" />
          <div className="absolute left-4 top-0 h-10 w-0.5 bg-white" />
          <div className="absolute left-2 top-6 h-0.5 w-5 bg-white" />
        </div>
      </Link>
      <div className="flex items-center gap-6 text-xl font-light tracking-wide text-[#b08f8f]">
        <Link href="/game" className="transition hover:text-[#8f6f6f]">
          Игра
        </Link>
        <button type="button" className="transition hover:text-[#8f6f6f]">
          Поддержать
        </button>
      </div>
    </div>
  );
}
