import { Header } from "../components/Header";
import { HanziMatchGame } from "../components/HanziMatchGame";

export default function GamePage() {
  return (
    <div className="min-h-screen w-full bg-[#d9d9d9] px-6 pb-6 pt-3 text-[#b08f8f]">
      <Header />
      <HanziMatchGame />
    </div>
  );
}
