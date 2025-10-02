from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LM = ROOT / "data" / "learning_materials"
PERF = ROOT / "data" / "performance"
LM.mkdir(parents=True, exist_ok=True)
PERF.mkdir(parents=True, exist_ok=True)

(LM / "Presentation_Skills_101.txt").write_text(
    "Structure: hook, agenda, 3 key points, demo, Q&A. Rehearse and timebox. Use stories and pain points.",
    encoding="utf-8"
)
(LM / "Client_Meetings.txt").write_text(
    "Before: research stakeholders/outcomes. During: confirm goals, ask clarifying questions, summarize decisions. After: recap with owners.",
    encoding="utf-8"
)

(PERF / "performance.csv").write_text(
    "employee_id,metric,score\n"
    "E001,presentation,48\n"
    "E001,email_clarity,62\n"
    "E001,client_meetings,55\n"
    "E001,time_management,71\n",
    encoding="utf-8"
)
print("Sample data written.")
