"use client";

import { useState } from "react";
import { DrawingPad } from "./components/DrawingPad";
import { ResultGrid } from "./components/ResultGrid";
import { SearchSidebar } from "./components/SearchSidebar";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const showResults = searchQuery.trim().length > 0;

  return (
    <div className="min-h-screen w-full bg-[#d9d9d9] px-6 pb-6 pt-3 text-[#b08f8f]">
      <Header />
      <div className="mb-10 flex gap-7">
        <DrawingPad />
        <SearchSidebar query={searchQuery} onQueryChange={setSearchQuery} />
      </div>
      {showResults ? <ResultGrid /> : null}
    </div>
  );
}

function Header() {
  return (
    <div className="mb-14 flex items-start justify-between">
      <div className="h-14 w-14 rounded-sm bg-[#b50709] p-2">
        <div className="relative h-full w-full">
          <div className="absolute left-0 top-1 h-0.5 w-7 bg-white" />
          <div className="absolute left-0 top-4 h-0.5 w-7 bg-white" />
          <div className="absolute left-4 top-0 h-10 w-0.5 bg-white" />
          <div className="absolute left-2 top-6 h-0.5 w-5 bg-white" />
        </div>
      </div>
      <button
        type="button"
        className="text-xl font-light tracking-wide text-[#b08f8f]"
      >
        Поддержать
      </button>
    </div>
  );
}
