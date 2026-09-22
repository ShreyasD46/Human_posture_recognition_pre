import { useCallback, useRef } from "react";

/**
 * Queue-based voice feedback using Web Speech API.
 *
 * - speakNow(text): cancels anything playing and speaks immediately (urgent corrections)
 * - speakAll(texts): queues up multiple corrections and plays them sequentially
 * - cancel(): silences everything and clears the queue
 *
 * Never blocks new, higher-priority corrections from being heard.
 */
export function useVoiceFeedback() {
  const queueRef = useRef([]);
  const speakingRef = useRef(false);

  const processQueue = useCallback(() => {
    if (speakingRef.current || !queueRef.current.length) return;
    if (!("speechSynthesis" in window)) return;

    const text = queueRef.current.shift();
    if (!text) { processQueue(); return; }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    speakingRef.current = true;
    utterance.onend = () => {
      speakingRef.current = false;
      processQueue(); // drain next in queue
    };
    utterance.onerror = () => {
      speakingRef.current = false;
      processQueue();
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  /** Cancel current speech, clear the queue, and speak this immediately. */
  const speakNow = useCallback((text) => {
    if (!("speechSynthesis" in window) || !text) return;
    window.speechSynthesis.cancel();
    speakingRef.current = false;
    queueRef.current = [];
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    speakingRef.current = true;
    utterance.onend = () => {
      speakingRef.current = false;
      processQueue();
    };
    utterance.onerror = () => {
      speakingRef.current = false;
      processQueue();
    };
    window.speechSynthesis.speak(utterance);
  }, [processQueue]);

  /** Queue multiple texts and start draining. Deduplicates with what's already queued. */
  const speakAll = useCallback((texts) => {
    if (!texts?.length) return;
    const existing = new Set(queueRef.current);
    for (const t of texts) {
      if (t && !existing.has(t)) {
        queueRef.current.push(t);
        existing.add(t);
      }
    }
    processQueue();
  }, [processQueue]);

  /** Speak a single text, appending to queue. */
  const speak = useCallback((text) => {
    if (text) speakAll([text]);
  }, [speakAll]);

  /** Cancel all speech and clear the queue. */
  const cancel = useCallback(() => {
    window.speechSynthesis?.cancel();
    speakingRef.current = false;
    queueRef.current = [];
  }, []);

  return { speak, speakNow, speakAll, cancel };
}
