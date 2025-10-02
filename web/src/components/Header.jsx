import React from "react";

export default function Header() {
  return (
    <div className="py-6">
      <h1 className="text-4xl font-extrabold tracking-tight">
        Personalized <span className="text-violet-400">AI Assistant</span>
      </h1>
      <p className="text-slate-300 mt-1">
        RAG • SQL • Translate • Mic • Voice • History
      </p>
    </div>
  );
}
