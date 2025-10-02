import React, { useState } from "react";
import { BACKEND_URL } from "../config";
import { hasSpeechRecognition, createRecognizer } from "../lib/speech";

export default function SqlPanel() {
  const [nl, setNl] = useState("");
  const [sql, setSql] = useState("");
  const [rows, setRows] = useState([]);
  const [cols, setCols] = useState([]);
  const [loadingGen, setLoadingGen] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);
  const [sttBusy, setSttBusy] = useState(false);

  const gen = async () => {
    setLoadingGen(true);
    try {
      const res = await fetch(`${BACKEND_URL}/sql/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: nl }),
      });
      const data = await res.json();
      setSql(data.sql || "");
    } catch (e) {
      setSql("-- failed: " + e.message);
    } finally {
      setLoadingGen(false);
    }
  };

  const run = async () => {
    setLoadingRun(true);
    try {
      const res = await fetch(`${BACKEND_URL}/sql/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql }),
      });
      const data = await res.json();
      setRows(data.rows || []);
      setCols(data.columns || []);
    } catch (e) {
      setRows([]);
      setCols([]);
      alert("SQL run failed: " + e.message);
    } finally {
      setLoadingRun(false);
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
      setNl(e.results[0][0].transcript);
      setSttBusy(false);
    };
    rec.onerror = () => setSttBusy(false);
    rec.onend = () => setSttBusy(false);
    rec.start();
  };

  return (
    <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-700">
      <div className="flex gap-2 mb-2 items-center">
        <input
          className="flex-1 px-3 py-2 rounded-lg bg-[#1e293b] text-white outline-none"
          placeholder="Ask: show recent files with most chunks"
          value={nl}
          onChange={(e) => setNl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && gen()}
        />
        <button
          className="px-3 py-2 rounded-lg bg-slate-600 hover:bg-slate-700 text-white"
          onClick={mic}
          title="Speak your SQL request"
          disabled={sttBusy}
        >
          {sttBusy ? "🎙️…" : "🎙️"}
        </button>
        <button
          className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
          onClick={gen}
          disabled={loadingGen}
        >
          {loadingGen ? "Generating…" : "Generate SQL"}
        </button>
      </div>

      <textarea
        className="w-full h-24 rounded-lg bg-[#111827] text-white p-2"
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        spellCheck={false}
      />

      <div className="mt-2">
        <button
          className="px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white"
          onClick={run}
          disabled={loadingRun}
        >
          {loadingRun ? "Running…" : "Run"}
        </button>
      </div>

      <div className="mt-3 overflow-auto">
        {rows.length > 0 && (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                {cols.map((c) => (
                  <th key={c} className="border-b border-slate-700 py-1 pr-4">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  {r.map((v, j) => (
                    <td key={j} className="border-b border-slate-800 py-1 pr-4">
                      {String(v)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {rows.length === 0 && (
          <div className="text-slate-400 text-sm">No results yet.</div>
        )}
      </div>
    </div>
  );
}
