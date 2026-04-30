import { NextResponse } from "next/server";

const ML_BASE_URL = process.env.ML_SERVICE_URL ?? "http://127.0.0.1:8000";

type Body = {
  query?: string;
  imageDataUrl?: string | null;
  filters?: {
    topK?: number;
    hskLevel?: number;
    strokesMin?: number;
    strokesMax?: number;
  };
};

async function readPayload(response: Response) {
  try {
    return await response.json();
  } catch {
    return { detail: response.statusText || "ML service returned invalid JSON", candidates: [] };
  }
}

function toBlobFromDataUrl(dataUrl: string): Blob {
  const [head, base64] = dataUrl.split(",", 2);
  const contentType = head.match(/data:(.*);base64/)?.[1] ?? "image/png";
  const bin = Buffer.from(base64 ?? "", "base64");
  return new Blob([bin], { type: contentType });
}

export async function POST(req: Request) {
  const body = (await req.json()) as Body;
  const filters = body.filters ?? {};
  const topK = filters.topK ?? 10;
  const params = new URLSearchParams({
    top_k: String(topK),
  });
  if (filters.hskLevel) params.set("hsk_level", String(filters.hskLevel));
  if (filters.strokesMin) params.set("strokes_min", String(filters.strokesMin));
  if (filters.strokesMax) params.set("strokes_max", String(filters.strokesMax));

  try {
    if (body.imageDataUrl) {
      const fd = new FormData();
      fd.append("image", toBlobFromDataUrl(body.imageDataUrl), "query.png");
      const response = await fetch(
        `${ML_BASE_URL}/search/by-image?${params.toString()}`,
        {
          method: "POST",
          body: fd,
        }
      );
      const payload = await readPayload(response);
      return NextResponse.json(payload, { status: response.status });
    }

    const q = (body.query ?? "").trim();
    if (!q) return NextResponse.json({ candidates: [] }, { status: 200 });

    params.set("q", q);
    const response = await fetch(
      `${ML_BASE_URL}/search/by-text?${params.toString()}`,
      { method: "GET" }
    );
    const payload = await readPayload(response);
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      {
        detail: error instanceof Error ? error.message : "ML service unavailable",
        candidates: [],
      },
      { status: 503 }
    );
  }
}

