import React, { useEffect, useState } from "react";
import { BACKEND_URL } from "../config";
import {
  hasSpeechRecognition,
  createRecognizer,
  speak,
  listVoices,
} from "../lib/speech";
import ChartView from "./ChartView";

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [parsed, setParsed] = useState(null);   // parsed JSON/chart
  const [mode, setMode] = useState("text");     // text | json | chart
  const [loading, setLoading] = useState(false);
  const [voices, setVoices] = useState([]);
  const [voiceName, setVoiceName] = useState("");

  useEffect(() => {
    const load = () => setVoices(listVoices());
    load();
    if ("speechSynthesis" in window) window.speechSynthesis.onvoiceschanged = load;
  }, []);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true); setAnswer(""); setParsed(null);
    try {
      const res = await fetch(`${BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, output_mode: mode }),
      });
      const data = await res.json();
      const text = data.answer || "";
      setAnswer(text);

      if (mode === "json" || mode === "chart") {
        // try parsing JSON body; handle cases where the model included extra prose
        let parsedObj = null;
        try {
          const start = text.indexOf("{");
          const end = text.lastIndexOf("}");
          const jsonSlice = start !== -1 && end !== -1 ? text.slice(start, end + 1) : text;
          parsedObj = JSON.parse(jsonSlice);
        } catch (_) {/* ignore */}
        setParsed(parsedObj);
      }
    } catch (e) {
      setAnswer("Failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const startSTT = () => {
    if (!hasSpeechRecognition)
      return alert("Speech Recognition not available in this browser.");
    const rec = createRecognizer();
    rec.onresult = (e) => setQuestion(e.results[0][0].transcript);
    rec.onerror = (e) => console.error(e);
    rec.start();
  };

  const speakOut = () => speak(answer, voiceName);

  return (
    <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-700">
      <div className="flex flex-col gap-3">
        <div className="flex gap-2 items-center">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask in RAG mode…"
            className="flex-1 px-3 py-2 rounded-lg bg-[#1e293b] text-white outline-none"
            onKeyDown={(e) => e.key === "Enter" && ask()}
          />
          <select
            className="bg-[#1e293b] text-white px-2 py-2 rounded-lg"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="text">Text</option>
            <option value="json">JSON</option>
            <option value="chart">Chart JSON</option>
          </select>
          <button
            onClick={ask}
            className="px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white"
            disabled={loading}
          >
            {loading ? "Asking…" : "Ask"}
          </button>
          <button
            onClick={startSTT}
            className="px-3 py-2 rounded-lg bg-slate-600 hover:bg-slate-700 text-white"
          >
            🎙️
          </button>
        </div>

        {/* Answer / JSON / Chart */}
        {mode === "chart" && parsed ? (
          <div className="rounded-lg p-3 bg-[#111827]">
            <ChartView spec={parsed.chart || parsed} />
            {parsed.answer && (
              <div className="mt-3 text-slate-100 whitespace-pre-wrap">{parsed.answer}</div>
            )}
          </div>
        ) : mode === "json" && parsed ? (
          <div className="rounded-lg p-3 bg-[#111827] text-slate-100 whitespace-pre-wrap">
            {JSON.stringify(parsed, null, 2)}
          </div>
        ) : (
          <div className="text-slate-100 whitespace-pre-wrap rounded-lg p-3 bg-[#111827] min-h-[120px]">
            {answer}
          </div>
        )}

        <div className="flex items-center gap-2">
          <select
            value={voiceName}
            onChange={(e) => setVoiceName(e.target.value)}
            className="bg-[#1e293b] text-white px-2 py-2 rounded-lg"
          >
            <option value="">Auto voice</option>
            {voices.map((v) => (
              <option key={v.name} value={v.name}>
                {v.name}
              </option>
            ))}
          </select>
          <button
            onClick={speakOut}
            className="px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            🔊 Speak
          </button>
        </div>
      </div>
    </div>
  );
}
