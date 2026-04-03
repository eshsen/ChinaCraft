"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Tool = "brush" | "eraser";

export function DrawingPad() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<Tool>("brush");
  const [brushSize, setBrushSize] = useState(4);
  const [eraserSize, setEraserSize] = useState(16);
  const drawing = useRef(false);
  const last = useRef<{ x: number; y: number } | null>(null);

  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    if (!canvas || !wrap) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    if (w < 2 || h < 2) return;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
  }, []);

  useEffect(() => {
    let inner = 0;
    const outer = requestAnimationFrame(() => {
      inner = requestAnimationFrame(() => initCanvas());
    });
    return () => {
      cancelAnimationFrame(outer);
      cancelAnimationFrame(inner);
    };
  }, [initCanvas]);

  const getPoint = useCallback(
    (clientX: number, clientY: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      const rect = canvas.getBoundingClientRect();
      return { x: clientX - rect.left, y: clientY - rect.top };
    },
    []
  );

  const drawSegment = useCallback(
    (from: { x: number; y: number }, to: { x: number; y: number }) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const size = tool === "brush" ? brushSize : eraserSize;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.lineWidth = size;
      ctx.strokeStyle = tool === "brush" ? "#1a1a1a" : "#ffffff";
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    },
    [tool, brushSize, eraserSize]
  );

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    drawing.current = true;
    const p = getPoint(e.clientX, e.clientY);
    if (p) last.current = p;
  };

  const onPointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    drawing.current = false;
    last.current = null;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current || !last.current) return;
    const p = getPoint(e.clientX, e.clientY);
    if (!p) return;
    drawSegment(last.current, p);
    last.current = p;
  };

  const clearAll = () => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    if (!canvas || !wrap) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
  };

  const sendPhoto = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const out = document.createElement("canvas");
    out.width = 128;
    out.height = 128;
    const octx = out.getContext("2d");
    if (!octx) return;
    octx.imageSmoothingEnabled = true;
    octx.imageSmoothingQuality = "high";
    octx.drawImage(canvas, 0, 0, 128, 128);
    const dataUrl = out.toDataURL("image/png");
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("chinacraft-drawing-128", {
          detail: { dataUrl, width: 128, height: 128 },
        })
      );
    }
  };

  return (
    <div className="w-[42%] min-w-[200px] shrink-0">
      <div className="rounded-[26px] bg-[#bcb6b8] p-5">
        <div
          ref={wrapRef}
          className="relative aspect-[4/3] w-full overflow-hidden rounded-[20px] bg-white"
        >
          <canvas
            ref={canvasRef}
            className="absolute inset-0 touch-none cursor-crosshair"
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
            onPointerMove={onPointerMove}
          />
        </div>
      </div>

      <div className="mt-3 flex justify-center gap-4">
        <button
          type="button"
          title="Кисточка"
          aria-label="Кисточка"
          onClick={() => setTool("brush")}
          className={`flex h-12 w-12 items-center justify-center rounded-full bg-[#ada8aa] transition ring-offset-2 ring-offset-[#d9d9d9] ${
            tool === "brush" ? "ring-2 ring-[#b50709]" : ""
          }`}
        >
          <span className="text-lg text-[#4a4547]">✎</span>
        </button>
        <button
          type="button"
          title="Ластик"
          aria-label="Ластик"
          onClick={() => setTool("eraser")}
          className={`flex h-12 w-12 items-center justify-center rounded-full bg-[#ada8aa] transition ring-offset-2 ring-offset-[#d9d9d9] ${
            tool === "eraser" ? "ring-2 ring-[#b50709]" : ""
          }`}
        >
          <span className="text-sm font-bold text-[#4a4547]">⌫</span>
        </button>
        <button
          type="button"
          title="Очистить всё"
          aria-label="Очистить всё"
          onClick={clearAll}
          className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ada8aa] text-xs font-medium text-[#4a4547]"
        >
          CLR
        </button>
      </div>

      <div className="mt-4 space-y-3 px-1">
        <label className="flex flex-col gap-1 text-xs tracking-wide text-[#8a7575]">
          <span>Размер кисточки</span>
          <input
            type="range"
            min={1}
            max={48}
            value={brushSize}
            onChange={(e) => setBrushSize(Number(e.target.value))}
            className="h-1 w-full cursor-pointer accent-[#b50709]"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs tracking-wide text-[#8a7575]">
          <span>Размер ластика</span>
          <input
            type="range"
            min={4}
            max={64}
            value={eraserSize}
            onChange={(e) => setEraserSize(Number(e.target.value))}
            className="h-1 w-full cursor-pointer accent-[#b50709]"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={sendPhoto}
        className="mt-4 w-full rounded-full bg-[#b50709] py-2.5 text-sm font-medium text-white transition hover:opacity-90"
      >
        Отправить фото
      </button>
    </div>
  );
}
