import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

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

let cachedEntries: HanziEntry[] | null = null;

function normalizePinyin(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
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

  if (!query) {
    return NextResponse.json({ entry: null });
  }

  const entries = await getEntries();
  const normalizedQuery = normalizePinyin(query);

  const byChar = entries.find((item) => item.char === query);
  const byPinyin =
    byChar ??
    entries.find((item) =>
      item.pinyin.some(
        (p) =>
          p.toLowerCase() === query.toLowerCase() ||
          normalizePinyin(p) === normalizedQuery
      )
    );

  return NextResponse.json({ entry: byPinyin ?? null });
}
