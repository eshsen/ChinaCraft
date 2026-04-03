"use client";

import { useCallback, useState } from "react";

type Props = {
  query: string;
  onQueryChange: (q: string) => void;
};

export function SearchSidebar({ query, onQueryChange }: Props) {
  const [history, setHistory] = useState<string[]>([]);

  const pushHistory = useCallback((raw: string) => {
    const t = raw.trim();
    if (!t) return;
    setHistory((h) => [t, ...h.filter((x) => x !== t)].slice(0, 30));
  }, []);

  const submitSearch = () => {
    pushHistory(query);
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

      <div className="mb-3 flex gap-3">
        {(["1", "2", "3"] as const).map((label) => (
          <button
            key={label}
            type="button"
            className="h-8 flex-1 rounded-full bg-[#ada8aa] text-sm text-[#5a5052] transition hover:bg-[#a39ea0]"
          >
            {label}
          </button>
        ))}
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
