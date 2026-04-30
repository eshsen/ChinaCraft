import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

type HanziEntry = {
  index: number;
  char: string;
  traditional?: string;
  strokes: number;
  pinyin: string[];
  radicals: string;
  frequency?: number;
  structure?: string;
  translation_ru: string;
  hsk_level?: number;
};

let cachedEntries: HanziEntry[] | null = null;

function normalizePinyin(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function getPinyinTone(value: string): number {
  if (/[āēīōūǖ]/i.test(value)) return 1;
  if (/[áéíóúǘ]/i.test(value)) return 2;
  if (/[ǎěǐǒǔǚ]/i.test(value)) return 3;
  if (/[àèìòùǜ]/i.test(value)) return 4;
  return 5;
}

function matchesTone(item: HanziEntry, tone?: number): boolean {
  if (!tone) return true;
  return item.pinyin.some((p) => getPinyinTone(p) === tone);
}

async function getEntries(): Promise<HanziEntry[]> {
  if (cachedEntries) return cachedEntries;
  const filePath = path.join(
    process.cwd(),
    "..",
    "SQL",
    "hanzi_with_translations.json"
  );
  const json = await readFile(filePath, "utf-8");
  cachedEntries = JSON.parse(json) as HanziEntry[];
  return cachedEntries;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = (searchParams.get("q") ?? "").trim();
  const limit = Math.min(
    Math.max(Number(searchParams.get("limit") ?? 8) || 8, 1),
    24
  );
  const tone = Number(searchParams.get("tone") ?? "") || undefined;

  if (!query) {
    return NextResponse.json({ entries: [] });
  }

  const entries = await getEntries();
  const normalizedQuery = normalizePinyin(query);

  const byChar = entries.filter(
    (item) => item.char === query && matchesTone(item, tone)
  );
  const exactPinyin = entries.filter((item) =>
    matchesTone(item, tone) &&
    item.pinyin.some(
      (p) =>
        p.toLowerCase() === query.toLowerCase() ||
        normalizePinyin(p) === normalizedQuery
    )
  );
  const containsPinyin = entries.filter((item) =>
    matchesTone(item, tone) &&
    item.pinyin.some((p) => normalizePinyin(p).includes(normalizedQuery))
  );

  const deduped = new Map<string, HanziEntry>();
  for (const item of [...byChar, ...exactPinyin, ...containsPinyin]) {
    if (!deduped.has(item.char)) {
      deduped.set(item.char, item);
    }
    if (deduped.size >= limit) break;
  }

  return NextResponse.json({ entries: Array.from(deduped.values()) });
}
