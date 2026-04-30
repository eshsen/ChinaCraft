"use client";

import { useCallback, useState } from "react";
import type { SearchFilters } from "../types/search";

type Props = {
  query: string;
  onQueryChange: (q: string) => void;
  filters: SearchFilters;
  onFiltersChange: (next: SearchFilters) => void;
  onSubmitText: () => void;
};

export function SearchSidebar({
  query,
  onQueryChange,
  filters,
  onFiltersChange,
  onSubmitText,
}: Props) {
  const [history, setHistory] = useState<string[]>([]);

  const pushHistory = useCallback((raw: string) => {
    const t = raw.trim();
    if (!t) return;
    setHistory((h) => [t, ...h.filter((x) => x !== t)].slice(0, 30));
  }, []);

  const submitSearch = () => {
    pushHistory(query);
    onSubmitText();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") submitSearch();
  };

  const pickHistory = (item: string) => {
    onQueryChange(item);
  };

  return (
    <div className="min-w-0 flex-1">
      <div className="mb-3 flex items-center gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Поиск…"
          className="h-10 min-w-0 flex-1 rounded-full border-0 bg-[#bcb6b8] px-5 text-[#4a3535] placeholder:text-[#9a8888] outline-none focus:ring-2 focus:ring-[#b50709]/40"
        />
        <button
          type="button"
          onClick={submitSearch}
          title="Поиск"
          aria-label="Поиск"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#bcb6b8] text-[#6a5555] transition hover:bg-[#ada8aa]"
        >
          <span className="text-lg">⌕</span>
        </button>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-3">
        <label className="text-xs text-[#5a5052]">
          Top-K
          <select
            value={filters.topK}
            onChange={(e) =>
              onFiltersChange({ ...filters, topK: Number(e.target.value) })
            }
            className="mt-1 h-8 w-full rounded-full bg-[#ada8aa] px-3 text-sm outline-none"
          >
            {[3, 6, 10, 12].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-[#5a5052]">
          HSK
          <select
            value={filters.hskLevel ?? ""}
            onChange={(e) =>
              onFiltersChange({
                ...filters,
                hskLevel: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="mt-1 h-8 w-full rounded-full bg-[#ada8aa] px-3 text-sm outline-none"
          >
            <option value="">Любой</option>
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <option key={n} value={n}>
                HSK {n}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-[#5a5052]">
          Мин. штрихов
          <input
            type="number"
            value={filters.strokesMin ?? ""}
            onChange={(e) =>
              onFiltersChange({
                ...filters,
                strokesMin: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="mt-1 h-8 w-full rounded-full bg-[#ada8aa] px-3 text-sm outline-none"
            min={1}
          />
        </label>
        <label className="text-xs text-[#5a5052]">
          Макс. штрихов
          <input
            type="number"
            value={filters.strokesMax ?? ""}
            onChange={(e) =>
              onFiltersChange({
                ...filters,
                strokesMax: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="mt-1 h-8 w-full rounded-full bg-[#ada8aa] px-3 text-sm outline-none"
            min={1}
          />
        </label>
      </div>

      <div className="max-h-[165px] overflow-y-auto rounded-[24px] bg-[#bcb6b8] p-3">
        <p className="mb-2 text-xs uppercase tracking-wider text-[#8a7575]">
          История
        </p>
        {history.length === 0 ? (
          <p className="text-sm text-[#9a8888]">Запросов пока нет</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {history.map((item) => (
              <li key={item}>
                <button
                  type="button"
                  onClick={() => pickHistory(item)}
                  className="w-full rounded-xl px-3 py-2 text-left text-sm text-[#4a3535] transition hover:bg-[#d9d9d9]/50"
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
