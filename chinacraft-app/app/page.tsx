export default function Home() {
  return (
    <main className="min-h-screen w-full bg-[#d9d9d9] px-6 pb-6 pt-3 text-[#b08f8f]">
      <header className="mb-14 flex items-start justify-between">
        <div className="h-14 w-14 rounded-sm bg-[#b50709] p-2">
          <div className="relative h-full w-full">
            <div className="absolute left-0 top-1 h-0.5 w-7 bg-white" />
            <div className="absolute left-0 top-4 h-0.5 w-7 bg-white" />
            <div className="absolute left-4 top-0 h-10 w-0.5 bg-white" />
            <div className="absolute left-2 top-6 h-0.5 w-5 bg-white" />
          </div>
        </div>
        <button className="text-xl font-light tracking-wide text-[#b08f8f]">
          Поддержать
        </button>
      </header>

      <section className="mb-10 flex gap-7">
        <div className="w-[42%]">
          <div className="rounded-[26px] bg-[#bcb6b8] p-5">
            <div className="h-[170px] w-full rounded-[20px] bg-[#d9d9d9]" />
          </div>
          <div className="mt-3 flex justify-center gap-4">
            <div className="h-12 w-12 rounded-full bg-[#ada8aa]" />
            <div className="h-12 w-12 rounded-full bg-[#ada8aa]" />
            <div className="h-12 w-12 rounded-full bg-[#ada8aa]" />
          </div>
        </div>

        <div className="w-[58%]">
          <div className="mb-3 flex items-center gap-3">
            <div className="h-10 flex-1 rounded-full bg-[#bcb6b8]" />
            <div className="h-10 w-10 rounded-full bg-[#bcb6b8]" />
          </div>
          <div className="mb-3 flex gap-3">
            <div className="h-8 flex-1 rounded-full bg-[#ada8aa]" />
            <div className="h-8 flex-1 rounded-full bg-[#ada8aa]" />
            <div className="h-8 flex-1 rounded-full bg-[#ada8aa]" />
          </div>
          <div className="h-[165px] rounded-[24px] bg-[#bcb6b8]" />
        </div>
      </section>

      <section className="grid grid-cols-3 gap-4">
        <div className="h-[180px] rounded-[22px] bg-[#b50709]" />
        <div className="h-[180px] rounded-[22px] bg-[#b2acaf]" />
        <div className="h-[180px] rounded-[22px] bg-[#b2acaf]" />
        <div className="h-[180px] rounded-[22px] bg-[#b2acaf]" />
        <div className="h-[180px] rounded-[22px] bg-[#b2acaf]" />
        <div className="h-[180px] rounded-[22px] bg-[#b2acaf]" />
      </section>
    </main>
  );
}
