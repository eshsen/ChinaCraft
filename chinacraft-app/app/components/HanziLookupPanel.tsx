"use client";

import { useEffect, useState } from "react";

type HanziEntry = {
  index: number;
  char: string;
  traditional?: string;
  strokes: number;
  pinyin: string[];
  radicals: string;
  frequency: number;
  structure: string;
  translation_ru: string;
  hsk_level?: number;
};

type HanziLookupResponse = {
  entries: HanziEntry[];
};

type Props = {
  query: string;
  trigger: number;
  showTranslations: boolean;
};

export function HanziLookupPanel({ query, trigger, showTranslations }: Props) {
  const [entries, setEntries] = useState<HanziEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setEntries([]);
      return;
    }

    const controller = new AbortController();
    const run = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/hanzi?q=${encodeURIComponent(trimmed)}&limit=8`,
          { signal: controller.signal }
        );
        if (!response.ok) throw new Error("lookup failed");
        const data = (await response.json()) as HanziLookupResponse;
        setEntries(data.entries ?? []);
      } catch {
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };

    run();
    return () => controller.abort();
  }, [query, trigger]);

  if (!query.trim()) return null;

  return (
    <section className="mb-6 rounded-[22px] bg-[#bcb6b8] p-4 text-[#4a3535]">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-medium tracking-wide">
          Результаты по пиньиню / иероглифу
        </h2>
        <span className="text-xs text-[#6f5d5d]">{entries.length} найдено</span>
      </div>

      {loading ? (
        <p className="rounded-2xl bg-[#d4cfd1] px-4 py-3 text-sm">Ищем...</p>
      ) : entries.length === 0 ? (
        <p className="rounded-2xl bg-[#d4cfd1] px-4 py-3 text-sm">
          По этому запросу точных совпадений не найдено.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {entries.map((entry) => (
            <article
              key={`${entry.char}-${entry.index}`}
              className="rounded-2xl bg-[#d4cfd1] p-4"
            >
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <div className="text-4xl leading-none">{entry.char}</div>
                  {entry.traditional ? (
                    <div className="mt-1 text-sm text-[#6f5d5d]">
                      Традиционный: {entry.traditional}
                    </div>
                  ) : null}
                </div>
                <div className="rounded-full bg-[#bcb6b8] px-3 py-1 text-xs">
                  HSK {entry.hsk_level ?? "—"}
                </div>
              </div>

              <div className="space-y-1 text-sm">
                <div>
                  <span className="text-[#6f5d5d]">Пиньинь:</span>{" "}
                  {entry.pinyin.join(", ")}
                </div>
                {showTranslations ? (
                  <div>
                    <span className="text-[#6f5d5d]">Перевод:</span>{" "}
                    {entry.translation_ru || "—"}
                  </div>
                ) : null}
                <div>
                  <span className="text-[#6f5d5d]">Ключ:</span>{" "}
                  {entry.radicals || "—"}
                </div>
                <div>
                  <span className="text-[#6f5d5d]">Штрихи:</span> {entry.strokes}
                </div>
                <div>
                  <span className="text-[#6f5d5d]">Структура:</span>{" "}
                  {entry.structure || "—"}
                </div>
                <div>
                  <span className="text-[#6f5d5d]">Частотность:</span>{" "}
                  {entry.frequency}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
