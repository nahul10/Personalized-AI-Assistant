/* web/src/lib/utils.ts
 * Utilities for networking, TTS (speech synthesis), and speech recognition.
 */

/* ------------------------------- Networking ------------------------------- */

export async function fetchJSON(
  url: string,
  opts: RequestInit = {},
  timeoutMs = 60_000
): Promise<any> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    const res = await fetch(url, { ...opts, signal: ctrl.signal });
    const raw = await res.text();
    let data: any = {};
    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        data = { raw };
      }
    }
    if (!res.ok) {
      // standardize error message so the UI can display something useful
      const msg =
        data?.detail ||
        data?.error ||
        data?.message ||
        (typeof data?.raw === "string" ? data.raw.slice(0, 400) : "") ||
        `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  } catch (err: any) {
    if (err?.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw new Error(err?.message || "Network error");
  } finally {
    clearTimeout(timer);
  }
}

export function postJSON(url: string, body: any, timeoutMs = 60_000) {
  return fetchJSON(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
  }, timeoutMs);
}

export function delay(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms));
}

/* ---------------------------- Language utilities --------------------------- */

/** Map UI language labels → BCP-47 tags that TTS/ASR understand. */
export const LANG_TO_TAG: Record<string, string> = {
  auto: "", // let the backend / browser decide
  english: "en-US",
  hindi: "hi-IN",
  tamil: "ta-IN",
  telugu: "te-IN",
  malayalam: "ml-IN",
  kannada: "kn-IN",
  bengali: "bn-IN",
  gujarati: "gu-IN",
  marathi: "mr-IN",
  urdu: "ur-PK",
  arabic: "ar-SA",
  french: "fr-FR",
  german: "de-DE",
  spanish: "es-ES",
  italian: "it-IT",
  chinese: "zh-CN",
  japanese: "ja-JP",
  korean: "ko-KR",
  russian: "ru-RU",
  turkish: "tr-TR",
  portuguese: "pt-BR",
};

export function normalizeLang(input?: string | null): string | undefined {
  if (!input) return undefined;
  const key = String(input).trim().toLowerCase();
  if (key === "auto") return undefined;
  // exact match by label
  if (LANG_TO_TAG[key]) return LANG_TO_TAG[key];
  // already a tag? pass through
  if (/^[a-z]{2,3}(-[A-Z]{2})?$/.test(key)) return input;
  return undefined;
}

/* -------------------------- Speech Synthesis (TTS) ------------------------- */

export type TTSSex = "male" | "female" | "auto";

let cachedVoices: SpeechSynthesisVoice[] | null = null;
let voicesPromise: Promise<SpeechSynthesisVoice[]> | null = null;

/** Load available voices (it may take time; browsers fire `voiceschanged`). */
export function getVoices(): Promise<SpeechSynthesisVoice[]> {
  if (cachedVoices && cachedVoices.length) {
    return Promise.resolve(cachedVoices);
  }
  if (voicesPromise) return voicesPromise;

  voicesPromise = new Promise((resolve) => {
    const synth = window.speechSynthesis;
    const tryResolve = () => {
      const v = synth.getVoices();
      if (v && v.length) {
        cachedVoices = v;
        resolve(v);
        return true;
      }
      return false;
    };

    if (tryResolve()) return;

    const onChange = () => {
      if (tryResolve()) {
        synth.removeEventListener?.("voiceschanged", onChange as any);
      }
    };
    synth.addEventListener?.("voiceschanged", onChange as any);

    // Fallback: attempt a few polls
    let attempts = 0;
    const poll = setInterval(() => {
      attempts += 1;
      if (tryResolve() || attempts > 10) {
        clearInterval(poll);
        synth.removeEventListener?.("voiceschanged", onChange as any);
        if (!cachedVoices) {
          cachedVoices = [];
          resolve([]);
        }
      }
    }, 250);
  });

  return voicesPromise;
}

/** Heuristic guess of voice “gender” based on the voice name/URI. */
function inferGender(v: SpeechSynthesisVoice): TTSSex {
  const n = (v.name + " " + v.voiceURI).toLowerCase();
  if (/\bf(emale)?\b|salli|susan|victoria|zira|nicky|helena|natasha|samantha|eva|female/.test(n)) {
    return "female";
  }
  if (/\bm(ale)?\b|daniel|alex|fred|george|thomas|xander|male/.test(n)) {
    return "male";
  }
  return "auto";
}

function startsWithLangTag(voiceLang: string, wanted?: string) {
  if (!wanted) return true;
  const v = voiceLang.toLowerCase();
  const w = wanted.toLowerCase();
  return v === w || v.startsWith(w.split("-")[0] + "-");
}

/** Choose a voice matching language + gender preference, with fallbacks. */
export function pickVoice(
  voices: SpeechSynthesisVoice[],
  langHint?: string,
  gender: TTSSex = "auto"
): SpeechSynthesisVoice | undefined {
  const wanted = langHint || "en-US";

  const byLang = voices.filter((v) => startsWithLangTag(v.lang || "", wanted));
  if (byLang.length) {
    if (gender !== "auto") {
      const g = byLang.find((v) => inferGender(v) === gender);
      if (g) return g;
    }
    return byLang[0];
  }

  // Fallback: any English voice
  const en = voices.filter((v) => startsWithLangTag(v.lang || "", "en-US"));
  if (en.length) {
    if (gender !== "auto") {
      const g = en.find((v) => inferGender(v) === gender);
      if (g) return g;
    }
    return en[0];
  }

  // Last resort: first available
  return voices[0];
}

export interface SpeakOptions {
  text: string;
  lang?: string;          // BCP-47 tag, e.g., "ta-IN"
  gender?: TTSSex;        // "auto" | "male" | "female"
  rate?: number;          // 0.5 .. 2.0 (default 1)
  pitch?: number;         // 0 .. 2 (default 1)
  volume?: number;        // 0 .. 1 (default 1)
}

/** Speak text; resolves when speech ends (or immediately if TTS is unavailable). */
export async function speak({
  text,
  lang,
  gender = "auto",
  rate = 1,
  pitch = 1,
  volume = 1,
}: SpeakOptions): Promise<void> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  if (!text || !text.trim()) return;

  // Cancel any current speech first
  stopSpeak();

  const voices = await getVoices();
  const voice = pickVoice(voices, lang, gender);

  const utter = new SpeechSynthesisUtterance(text);
  if (voice) utter.voice = voice;
  utter.lang = lang || voice?.lang || "en-US";
  utter.rate = rate;
  utter.pitch = pitch;
  utter.volume = volume;

  await new Promise<void>((resolve) => {
    utter.onend = () => resolve();
    utter.onerror = () => resolve(); // don’t reject – fail silently
    window.speechSynthesis.speak(utter);
  });
}

export function stopSpeak() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

export function canSpeak(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/* --------------------------- Speech Recognition ---------------------------- */

declare global {
  interface Window {
    webkitSpeechRecognition?: any;
  }
}

export interface Recognizer {
  start: () => void;
  stop: () => void;
  abort: () => void;
  setLang: (tag?: string) => void;
  onResult?: (finalText: string, isFinal: boolean) => void;
  onError?: (err: string) => void;
}

/**
 * Create a simple wrapper around the Web Speech API (if available).
 * Use: const rec = createRecognizer({ lang: 'ta-IN' }); rec.start();
 */
export function createRecognizer(options?: { lang?: string; interim?: boolean }): Recognizer | null {
  const SpeechRec = (window as any).SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return null;

  const rec = new SpeechRec();
  rec.continuous = true;
  rec.interimResults = !!options?.interim;
  rec.lang = options?.lang || "en-US";

  const wrapper: Recognizer = {
    start: () => {
      try { rec.start(); } catch { /* already started */ }
    },
    stop: () => rec.stop(),
    abort: () => rec.abort(),
    setLang: (tag?: string) => { rec.lang = tag || "en-US"; },
    onResult: undefined,
    onError: undefined,
  };

  rec.onresult = (ev: any) => {
    let finalText = "";
    let isFinal = false;
    for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
      const r = ev.results[i];
      finalText += r[0].transcript;
      if (r.isFinal) isFinal = true;
    }
    wrapper.onResult?.(finalText, isFinal);
  };

  rec.onerror = (e: any) => {
    const msg = e?.error || "mic-error";
    wrapper.onError?.(msg);
  };

  return wrapper;
}

/* ------------------------------- Convenience ------------------------------- */

/** Turn a UI language label into a TTS/ASR tag; returns undefined for Auto. */
export function langLabelToTag(label?: string | null): string | undefined {
  if (!label) return undefined;
  return normalizeLang(label);
}

/** Most browsers benefit from a user gesture before TTS can play. */
export async function ensureAudioUnlocked() {
  try {
    // On some mobile browsers, a zero-length utterance helps unlock audio.
    if (canSpeak()) {
      const u = new SpeechSynthesisUtterance(" ");
      window.speechSynthesis.speak(u);
      window.speechSynthesis.cancel();
    }
  } catch {
    /* ignore */
  }
}
