import { useCallback, useState } from "react";

const UNLOCKED_KEY = "signal_gate_unlocked";
const DISMISSED_KEY = "signal_gate_dismissed";

export function useGate() {
  const [unlocked, setUnlocked] = useState<boolean>(() => localStorage.getItem(UNLOCKED_KEY) === "1");
  const [dismissed, setDismissed] = useState<boolean>(() => localStorage.getItem(DISMISSED_KEY) === "1");

  const unlock = useCallback(() => {
    localStorage.setItem(UNLOCKED_KEY, "1");
    setUnlocked(true);
  }, []);

  const dismiss = useCallback(() => {
    localStorage.setItem(DISMISSED_KEY, "1");
    setDismissed(true);
  }, []);

  return { locked: !unlocked && !dismissed, unlock, dismiss };
}
