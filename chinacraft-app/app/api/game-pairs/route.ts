import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

type GameMode = "translation" | "pinyin";

type HanziGameEntry = {
  char: string;
  pinyin: string[];
  translation_ru: string;
  strokes?: number;
  hsk_level?: number;
};

type HanziGamePair = {
  id: string;
  similarity: number;
  left: HanziGameEntry;
  right: HanziGameEntry;
};

type GamePairsFile = {
  pair_count: number;
  pairs: HanziGamePair[];
};

let cachedPairs: HanziGamePair[] | null = null;

async function getPairs(): Promise<HanziGamePair[]> {
  if (cachedPairs) return cachedPairs;
  const filePath = path.join(
    process.cwd(),
    "..",
    "SQL",
    "hanzi_similarity_game_pairs.json"
  );
  const json = await readFile(filePath, "utf-8");
  cachedPairs = (JSON.parse(json) as GamePairsFile).pairs ?? [];
  return cachedPairs;
}

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function pickMode(raw: string | null): GameMode {
  if (raw === "translation" || raw === "pinyin") return raw;
  return Math.random() < 0.5 ? "translation" : "pinyin";
}

function labelFor(entry: HanziGameEntry, mode: GameMode): string {
  return mode === "translation"
    ? entry.translation_ru
    : entry.pinyin.join(", ");
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const mode = pickMode(searchParams.get("mode"));
  const pairs = await getPairs();
  const validPairs = pairs.filter(
    (pair) => labelFor(pair.left, mode) !== labelFor(pair.right, mode)
  );

  if (validPairs.length === 0) {
    return NextResponse.json(
      { detail: "No game pairs available for this mode." },
      { status: 404 }
    );
  }

  const pair = validPairs[Math.floor(Math.random() * validPairs.length)];
  const cards = [
    { id: "left", ...pair.left },
    { id: "right", ...pair.right },
  ];
  const options = shuffle(
    cards.map((card) => ({
      id: card.id,
      label: labelFor(card, mode),
    }))
  );

  return NextResponse.json({
    id: pair.id,
    mode,
    similarity: pair.similarity,
    cards,
    options,
  });
}
