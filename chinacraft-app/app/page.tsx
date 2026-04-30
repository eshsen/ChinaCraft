"use client";

import { useState } from "react";
import { DrawingPad } from "./components/DrawingPad";
import { Header } from "./components/Header";
import { HanziLookupPanel } from "./components/HanziLookupPanel";
import { ResultGrid } from "./components/ResultGrid";
import { SearchSidebar } from "./components/SearchSidebar";
import type { SearchFilters } from "./types/search";

function containsHanzi(value: string): boolean {
  return /[\u3400-\u9fff]/.test(value);
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [submittedImage, setSubmittedImage] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);
  const [filters, setFilters] = useState<SearchFilters>({ topK: 10 });
  const [showTranslations, setShowTranslations] = useState(true);
  const canSearchSimilar =
    Boolean(submittedImage) || containsHanzi(submittedQuery.trim());
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

  const pickHanzi = (char: string) => {
    setSearchQuery(char);
    setSubmittedImage(null);
    setSubmittedQuery(char);
    setTrigger((v) => v + 1);
  };

  return (
    <div className="min-h-screen w-full bg-[#d9d9d9] px-6 pb-6 pt-3 text-[#b08f8f]">
      <Header />
      <div className="mb-10 flex gap-7">
        <DrawingPad
          onSubmitImage={submitImage}
          showTranslations={showTranslations}
          onToggleTranslations={() => setShowTranslations((value) => !value)}
        />
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
          <HanziLookupPanel
            query={submittedQuery}
            trigger={trigger}
            tone={filters.tone}
            showTranslations={showTranslations}
            onPickHanzi={pickHanzi}
          />
          {canSearchSimilar ? (
            <ResultGrid
              query={submittedQuery}
              imageDataUrl={submittedImage}
              trigger={trigger}
              filters={filters}
              showTranslations={showTranslations}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
