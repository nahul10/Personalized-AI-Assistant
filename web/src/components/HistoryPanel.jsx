import React, { useEffect, useState } from "react";
import { BACKEND_URL } from "../config";

export default function HistoryPanel() {
  const [items, setItems] = useState([]);

  const load = async () => {
    const res = await fetch(`${BACKEND_URL}/history`);
    const data = await res.json();
    setItems(data);
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-700">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold">History</h3>
        <button
          className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600"
          onClick={load}
        >
          Refresh
        </button>
      </div>
      <div className="space-y-2 max-h-[320px] overflow-auto">
        {items.map((it) => (
          <div key={it.id} className="p-2 rounded-lg bg-[#111827]">
            <div className="text-xs text-slate-400">
              {it.mode} • {new Date(it.created_at).toLocaleString()}
            </div>
            <div className="font-medium mt-1">{it.question}</div>
            <div className="text-sm mt-1 text-slate-200 line-clamp-3">
              {it.answer}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
