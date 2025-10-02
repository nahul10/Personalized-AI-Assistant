import React, { useState } from "react";
import Header from "./components/Header";
import PdfUploader from "./components/PdfUploader";
import ChatBox from "./components/ChatBox";
import SqlPanel from "./components/SqlPanel";
import TranslatePanel from "./components/TranslatePanel";
import HistoryPanel from "./components/HistoryPanel";
import "./App.css";

export default function App() {
  const [active, setActive] = useState("rag");

  const Tab = ({id, label}) => (
    <button
      onClick={()=>setActive(id)}
      className={`px-3 py-2 rounded-lg ${active===id ? "bg-violet-600 text-white" : "bg-[#121826] text-slate-200 hover:bg-[#1a2233]"}`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-[#0b1220] text-white">
      <div className="max-w-6xl mx-auto px-4">
        <Header />

        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 space-y-4">
            <PdfUploader />
            <div className="flex gap-2">
              <Tab id="rag" label="RAG" />
              <Tab id="sql" label="SQL" />
              <Tab id="translate" label="TRANSLATE" />
            </div>
            {active==="rag" && <ChatBox />}
            {active==="sql" && <SqlPanel />}
            {active==="translate" && <TranslatePanel />}
          </div>

          <div className="w-full lg:w-[28rem]">
            <HistoryPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
