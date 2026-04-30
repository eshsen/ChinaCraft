"use client";

import { useEffect, useMemo, useState } from "react";

type GameMode = "translation" | "pinyin";

type GameCard = {
  id: "left" | "right";
  char: string;
  pinyin: string[];
  translation_ru: string;
  strokes?: number;
  hsk_level?: number;
};

type GameOption = {
  id: "left" | "right";
  label: string;
};

type GameTask = {
  id: string;
  mode: GameMode;
  similarity: number;
  cards: GameCard[];
  options: GameOption[];
};

type ChoiceState = Partial<Record<GameCard["id"], GameOption["id"]>>;

const MODE_LABEL: Record<GameMode, string> = {
  translation: "перевод",
  pinyin: "пиньинь",
};

export function HanziMatchGame() {
  const [task, setTask] = useState<GameTask | null>(null);
  const [choices, setChoices] = useState<ChoiceState>({});
  const [checked, setChecked] = useState(false);
  const [mode, setMode] = useState<"mixed" | GameMode>("mixed");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const correctCount = useMemo(() => {
    if (!task) return 0;
    return task.cards.filter((card) => choices[card.id] === card.id).length;
  }, [choices, task]);

  const loadTask = async (nextMode = mode) => {
    try {
      setLoading(true);
      setError("");
      setChecked(false);
      setChoices({});
      const response = await fetch(`/api/game-pairs?mode=${nextMode}`);
      if (!response.ok) throw new Error("game task failed");
      const data = (await response.json()) as GameTask;
      setTask(data);
    } catch {
      setTask(null);
      setError("Не удалось загрузить задание.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setCardChoice = (cardId: GameCard["id"], optionId: GameOption["id"]) => {
    if (checked) return;
    setChoices((value) => ({ ...value, [cardId]: optionId }));
  };

  const changeMode = (nextMode: typeof mode) => {
    setMode(nextMode);
    loadTask(nextMode);
  };

  const allAnswered = task ? task.cards.every((card) => choices[card.id]) : false;

  return (
    <section className="rounded-[26px] bg-[#bcb6b8] p-5 text-[#4a3535]">
      <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-medium text-[#4a3535]">
            Игра на похожие иероглифы
          </h1>
          <p className="mt-1 text-sm text-[#6f5d5d]">
            Сопоставьте каждый иероглиф с его переводом или пиньинем.
          </p>
        </div>
        <div className="flex gap-2">
          {(["mixed", "translation", "pinyin"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => changeMode(item)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                mode === item
                  ? "bg-[#b50709] text-white"
                  : "bg-[#d4cfd1] text-[#4a3535] hover:bg-[#c9c1c4]"
              }`}
            >
              {item === "mixed"
                ? "Случайно"
                : item === "translation"
                  ? "Перевод"
                  : "Пиньинь"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="rounded-2xl bg-[#d4cfd1] p-6">Загрузка...</div>
      ) : error ? (
        <div className="rounded-2xl bg-[#d4cfd1] p-6">{error}</div>
      ) : task ? (
        <>
          <div className="mb-4 rounded-2xl bg-[#d4cfd1] p-3 text-sm text-[#6f5d5d]">
            Тип задания: {MODE_LABEL[task.mode]}. Схожесть пары:{" "}
            {(task.similarity * 100).toFixed(1)}%.
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {task.cards.map((card) => (
              <article key={card.id} className="rounded-[22px] bg-[#d4cfd1] p-5">
                <div className="mb-4 text-center text-8xl leading-none text-[#4a3535]">
                  {card.char}
                </div>
                <div className="mb-4 flex justify-center gap-2 text-xs text-[#6f5d5d]">
                  <span>HSK {card.hsk_level ?? "—"}</span>
                  <span>Штрихи: {card.strokes ?? "—"}</span>
                </div>
                <div className="grid gap-2">
                  {task.options.map((option) => {
                    const selected = choices[card.id] === option.id;
                    const isCorrect = checked && option.id === card.id;
                    const isWrong = checked && selected && option.id !== card.id;
                    return (
                      <button
                        key={`${card.id}-${option.id}`}
                        type="button"
                        onClick={() => setCardChoice(card.id, option.id)}
                        className={`rounded-2xl px-4 py-3 text-sm font-medium transition ${
                          isCorrect
                            ? "bg-green-600 text-white"
                            : isWrong
                              ? "bg-[#b50709] text-white"
                              : selected
                                ? "bg-[#4a3535] text-white"
                                : "bg-[#bcb6b8] text-[#4a3535] hover:bg-[#ada8aa]"
                        }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>

          <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="text-sm text-[#6f5d5d]">
              {checked
                ? `Правильно: ${correctCount} из ${task.cards.length}`
                : "Выберите ответ для каждого иероглифа."}
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                disabled={!allAnswered || checked}
                onClick={() => setChecked(true)}
                className="rounded-full bg-[#b50709] px-5 py-2.5 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Проверить
              </button>
              <button
                type="button"
                onClick={() => loadTask()}
                className="rounded-full bg-[#d4cfd1] px-5 py-2.5 text-sm font-medium text-[#4a3535] transition hover:bg-[#c9c1c4]"
              >
                Следующая пара
              </button>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
