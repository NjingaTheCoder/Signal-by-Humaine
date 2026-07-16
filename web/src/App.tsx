import { useState } from "react";
import { Nav } from "./components/Nav";
import { Strapline } from "./components/Strapline";
import { Footer } from "./components/Footer";
import { Briefing } from "./components/Briefing";
import { NewsFeed } from "./components/NewsFeed";
import { Funding } from "./components/Funding";
import { Tenders } from "./components/Tenders";
import { Markets } from "./components/Markets";
import { Careers } from "./components/Careers";
import { Resources } from "./components/Resources";
import { GateModal } from "./components/GateModal";
import { GatedSection } from "./components/GatedSection";
import { useGate } from "./lib/useGate";

export default function App() {
  const { locked, unlock, dismiss } = useGate();
  const [modalOpen, setModalOpen] = useState(false);

  function requestUnlock() {
    setModalOpen(true);
  }

  return (
    <>
      <Nav />
      <Strapline />
      <Briefing />
      <NewsFeed gated={locked} onRequestUnlock={requestUnlock} />
      <GatedSection locked={locked} onRequestUnlock={requestUnlock}>
        <Funding />
        <Tenders />
        <Markets />
        <Careers />
        <Resources />
      </GatedSection>
      <Footer />
      {modalOpen && (
        <GateModal
          onClose={() => {
            dismiss();
            setModalOpen(false);
          }}
          onUnlock={() => {
            unlock();
            setModalOpen(false);
          }}
        />
      )}
    </>
  );
}
