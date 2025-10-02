import React, { useState } from "react";
import { BACKEND_URL } from "../config";

export default function PdfUploader({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");

  const upload = async () => {
    if (!file) { setMsg("Please choose a file first."); return; }
    const fd = new FormData();
    fd.append("file", file);
    setMsg("Uploading…");
    try {
      const res = await fetch(`${BACKEND_URL}/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
      setMsg(`✅ ${data.detail.filename} • pages=${data.detail.pages} • chunks=${data.detail.chunks}`);
      onUploaded?.(data.detail);
    } catch (e) {
      setMsg("❌ " + e.message);
    }
  };

  const resetIndex = async (alsoHistory=false) => {
    try {
      const res = await fetch(`${BACKEND_URL}/reset_index`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ delete_history: alsoHistory })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
      setMsg(`🧹 Index reset${data.deleted_history ? " (history cleared)" : ""}.`);
    } catch (e) {
      setMsg("❌ Reset failed: " + e.message);
    }
  };

  return (
    <div className="p-4 rounded-2xl bg-[#121826] border border-slate-700">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".pdf,.docx,.png,.jpg,.jpeg,.webp,.txt"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button
          onClick={upload}
          className="px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white"
        >
          Upload & Ingest
        </button>

        <div className="ml-auto flex gap-2">
          <button
            onClick={() => resetIndex(false)}
            className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
            title="Remove files and chunks only"
          >
            Reset Index
          </button>
          <button
            onClick={() => resetIndex(true)}
            className="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white"
            title="Also clear history"
          >
            Reset + History
          </button>
        </div>
      </div>
      <div className="mt-2 text-sm text-slate-200">{msg}</div>
    </div>
  );
}
