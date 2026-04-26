"use client";

import { useState } from "react";
import { DrawingPad } from "./components/DrawingPad";
import { HanziLookupPanel } from "./components/HanziLookupPanel";
import { ResultGrid } from "./components/ResultGrid";
import { SearchSidebar } from "./components/SearchSidebar";
import type { SearchFilters } from "./types/search";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [submittedImage, setSubmittedImage] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);
  const [filters, setFilters] = useState<SearchFilters>({ topK: 6 });
  const showResults = submittedQuery.trim().length > 0 || Boolean(submittedImage);

  const submitText = () => {
    setSubmittedImage(null);
    setSubmittedQuery(searchQuery.trim());
    setTrigger((v) => v + 1);
  };

  const submitImage = (dataUrl: string) => {
    setSubmittedImage(dataUrl);
    setSubmittedQuery(searchQuery.trim());
    setTrigger((v) => v + 1);
  };

  return (
    <div className="min-h-screen w-full bg-[#d9d9d9] px-6 pb-6 pt-3 text-[#b08f8f]">
      <Header />
      <div className="mb-10 flex gap-7">
        <DrawingPad onSubmitImage={submitImage} />
        <SearchSidebar
          query={searchQuery}
          onQueryChange={setSearchQuery}
          filters={filters}
          onFiltersChange={setFilters}
          onSubmitText={submitText}
        />
      </div>
      {showResults ? (
        <>
          <HanziLookupPanel query={submittedQuery} trigger={trigger} />
          <ResultGrid
            query={submittedQuery}
            imageDataUrl={submittedImage}
            trigger={trigger}
            filters={filters}
          />
        </>
      ) : null}
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
