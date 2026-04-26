"use client";

import { useEffect, useState } from "react";
import type { SearchFilters, SearchResponse } from "../types/search";

type Props = {
  query: string;
  imageDataUrl: string | null;
  filters: SearchFilters;
  trigger: number;
};

export function ResultGrid({ query, imageDataUrl, filters, trigger }: Props) {
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed && !imageDataUrl) {
      setResult(null);
      return;
    }

    const controller = new AbortController();
    const run = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/similar", {
          method: "POST",
          signal: controller.signal,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: trimmed,
            imageDataUrl,
            filters,
          }),
        });
        if (!response.ok) throw new Error("search failed");
        const data = (await response.json()) as SearchResponse;
        setResult(data);
      } catch {
        setResult(null);
      } finally {
        setLoading(false);
      }
    };

    run();
    return () => controller.abort();
  }, [query, imageDataUrl, trigger, filters]);

  if (loading) {
    return (
      <section className="grid grid-cols-1">
        <div className="w-full rounded-[22px] bg-[#b2acaf] p-6 text-[#4a3535]">
          Поиск...
        </div>
      </section>
    );
  }

  if (!result || result.candidates.length === 0) {
    return (
      <section className="grid grid-cols-1">
        <div className="w-full rounded-[22px] bg-[#b2acaf] p-6 text-[#4a3535]">
          Ничего не найдено.
        </div>
      </section>
    );
  }

  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {result.candidates.map((item, idx) => (
        <article
          key={`${item.char}-${idx}`}
          className={`rounded-[22px] p-6 ${
            idx === 0 ? "bg-[#b50709] text-white" : "bg-[#b2acaf] text-[#4a3535]"
          }`}
        >
          <div className="mb-3 text-6xl leading-none">{item.char}</div>
          <div className="space-y-1 text-sm">
            <div>Схожесть: {(item.score * 100).toFixed(1)}%</div>
            <div>Пиньинь: {item.pinyin?.join(", ") || "—"}</div>
            <div>HSK: {item.hsk_level ?? "—"}</div>
            <div>Штрихи: {item.strokes ?? "—"}</div>
            <div>Перевод: {item.translation_ru || "—"}</div>
          </div>
          {item.sample_image ? (
            <div className="mt-3 truncate text-xs opacity-75">{item.sample_image}</div>
          ) : null}
        </article>
      ))}
      <div className="col-span-full rounded-[22px] bg-[#bcb6b8] p-3 text-xs text-[#5a5052]">
        model={result.model_version}; index={result.index_version}; mode=
        {result.query_type}
      </div>
    </section>
  );
}
