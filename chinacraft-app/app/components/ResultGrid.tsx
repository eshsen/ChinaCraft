"use client";

import { useEffect, useState } from "react";

type HanziEntry = {
  index: number;
  char: string;
  strokes: number;
  pinyin: string[];
  radicals: string;
  frequency: number;
  structure: string;
  translation_ru: string;
  hsk_level: number;
};

type Props = {
  query: string;
};

export function ResultGrid({ query }: Props) {
  const [entry, setEntry] = useState<HanziEntry | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setEntry(null);
      return;
    }

    const controller = new AbortController();
    const run = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/hanzi?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal }
        );
        const data = (await response.json()) as { entry: HanziEntry | null };
        setEntry(data.entry);
      } catch {
        setEntry(null);
      } finally {
        setLoading(false);
      }
    };

    run();
    return () => controller.abort();
  }, [query]);

  if (loading) {
    return (
      <section className="grid grid-cols-1">
        <div className="w-full rounded-[22px] bg-[#b2acaf] p-6 text-[#4a3535]">
          Поиск...
        </div>
      </section>
    );
  }

  if (!entry) {
    return (
      <section className="grid grid-cols-1">
        <div className="w-full rounded-[22px] bg-[#b2acaf] p-6 text-[#4a3535]">
          Ничего не найдено по запросу &quot;{query}&quot;.
        </div>
      </section>
    );
  }

  const infoRows: Array<[string, string | number]> = [
    ["Пиньинь", entry.pinyin.join(", ")],
    ["Штрихи", entry.strokes],
    ["Радикалы", entry.radicals],
    ["Встречаемость", entry.frequency],
    ["Структура", entry.structure],
    ["Перевод", entry.translation_ru],
    ["HSK уровень", entry.hsk_level],
  ];

  return (
    <section className="grid grid-cols-1">
      <div className="w-full rounded-[22px] bg-[#b50709] p-6 text-white">
        <div className="mb-5 text-7xl leading-none">{entry.char}</div>
        <div className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
          {infoRows.map(([label, value]) => (
            <div
              key={label}
              className="rounded-lg bg-white/10 px-3 py-2 backdrop-blur-[1px]"
            >
              <span className="mr-2 text-white/75">{label}:</span>
              <span>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
