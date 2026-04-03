"use client";

const PLACEHOLDER_COUNT = 6;

export function ResultGrid() {
  return (
    <section className="grid grid-cols-3 gap-4">
      {Array.from({ length: PLACEHOLDER_COUNT }, (_, i) => (
        <div
          key={i}
          className={`w-full overflow-hidden rounded-[22px] ${
            i === 0 ? "bg-[#b50709]" : "bg-[#b2acaf]"
          }`}
          style={{ aspectRatio: "3 / 4" }}
        />
      ))}
    </section>
  );
}
