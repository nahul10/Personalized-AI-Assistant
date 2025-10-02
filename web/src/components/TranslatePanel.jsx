import React, { useMemo, useState } from "react";
import { BACKEND_URL } from "../config";
import { speak, hasSpeechRecognition, createRecognizer } from "../lib/speech";

const LANGS = [
  // Common + Indian + world languages
  { code: "en", name: "English" },
  { code: "ta", name: "Tamil" },
  { code: "hi", name: "Hindi" },
  { code: "te", name: "Telugu" },
  { code: "mr", name: "Marathi" },
  { code: "bn", name: "Bengali" },
  { code: "ml", name: "Malayalam" },
  { code: "gu", name: "Gujarati" },
  { code: "kn", name: "Kannada" },
  { code: "pa", name: "Punjabi" },
  { code: "ur", name: "Urdu" },
  { code: "ne", name: "Nepali" },

  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "es", name: "Spanish" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "tr", name: "Turkish" },
  { code: "ar", name: "Arabic" },
  { code: "fa", name: "Persian" },
  { code: "ru", name: "Russian" },
  { code: "uk", name: "Ukrainian" },
  { code: "pl", name: "Polish" },
  { code: "nl", name: "Dutch" },
  { code: "sv", name: "Swedish" },
  { code: "da", name: "Danish" },
  { code: "no", name: "Norwegian" },
  { code: "fi", name: "Finnish" },
  { code: "cs", name: "Czech" },
  { code: "ro", name: "Romanian" },
  { code: "hu", name: "Hungarian" },
  { code: "sk", name: "Slovak" },
  { code: "el", name: "Greek" },
  { code: "he", name: "Hebrew" },

  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese (Simplified)" },
  { code: "vi", name: "Vietnamese" },
  { code: "th", name: "Thai" },
  { code: "id", name: "Indonesian" },
];

export default function TranslatePanel() {
  const [text, setText] = useState("");
  const [from, setFrom] = useState("auto");  // UI-only; backend just needs target
  const [lang, setLang] = useState("ta");
  const [out, setOut] = useState("");
  const [busy, setBusy] = useState(false);
  const [sttBusy, setSttBusy] = useState(false);

  const options = useMemo(
    () => LANGS.map((l) => <option key={l.code} value={l.code}>{l.name}</option>),
    []
  );

  const doTranslate = async () => {
    if (!text.trim()) return;
    setBusy(true);
    try {
      // (Optional) hint the backend with the source language in the text
      const payload = {
        text: from === "auto" ? text : `[source=${from}] ${text}`,
        target_lang: lang,
      };
      const res = await fetch(`${BACKEND_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setOut(data.translation || "");
    } catch (e) {
      setOut("Translate failed: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  const mic = () => {
    if (!hasSpeechRecognition) {
      alert("Speech Recognition not available in this browser.");
      return;
    }
    const rec = createRecognizer();
    setSttBusy(true);
    rec.onresult = (e) => {
      setText(e.results[0][0].transcript);
      setSttBusy(false);
    };
    rec.onerror = () => setSttBusy(false);
    rec.onend = () => setSttBusy(false);
    rec.start();
  };

  const swap = () => {
    if (from === "auto") return; // can't swap when auto-detect
    const prevFrom = from;
    setFrom(lang);
    setLang(prevFrom);
    if (out) setText(out);
    setOut("");
  };

  return (
    <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-700">
      <div className="flex flex-wrap gap-2 items-center mb-3">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-300">From</label>
          <select
            className="bg-[#1e293b] text-white px-2 py-2 rounded-lg"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          >
            <option value="auto">Auto-detect</option>
            {options}
          </select>
        </div>

        <button
          className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
          onClick={swap}
          title="Swap languages"
          disabled={from === "auto"}
        >
          ⇄ Swap
        </button>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-300">To</label>
          <select
            className="bg-[#1e293b] text-white px-2 py-2 rounded-lg"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
          >
            {options}
          </select>
        </div>

        <button
          className="px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white"
          onClick={doTranslate}
          disabled={busy}
        >
          {busy ? "Translating…" : "Translate"}
        </button>
      </div>

      <div className="flex gap-2 items-start mb-2">
        <textarea
          className="w-full h-28 rounded-lg bg-[#111827] text-white p-2"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Speak or type text to translate…"
        />
        <button
          className="px-3 py-2 rounded-lg bg-slate-600 hover:bg-slate-700 text-white"
          onClick={mic}
          disabled={sttBusy}
          title="Dictate source text"
        >
          {sttBusy ? "🎙️…" : "🎙️"}
        </button>
      </div>

      <div className="bg-[#111827] rounded-lg p-2 min-h-[90px] whitespace-pre-wrap">
        {out}
      </div>

      <div className="mt-2 flex gap-2">
        <button
          onClick={() => speak(out)}
          className="px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white"
          disabled={!out}
          title="Speak translation"
        >
          🔊 Speak
        </button>
        <button
          onClick={() => { navigator.clipboard.writeText(out || ""); }}
          className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
          disabled={!out}
          title="Copy translation"
        >
          📋 Copy
        </button>
      </div>
    </div>
  );
}
