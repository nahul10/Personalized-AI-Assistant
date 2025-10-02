// Browser speech utilities (no server audio).
export const hasSpeechRecognition = "webkitSpeechRecognition" in window || "SpeechRecognition" in window;
export const hasSpeechSynthesis = "speechSynthesis" in window;

export function createRecognizer(lang = "en-US") {
  const R = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!R) return null;
  const rec = new R();
  rec.lang = lang;
  rec.interimResults = false;
  rec.continuous = false;
  return rec;
}

export function speak(text, voiceName) {
  if (!hasSpeechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  if (voiceName) {
    const voices = window.speechSynthesis.getVoices();
    const v = voices.find(v => v.name === voiceName);
    if (v) u.voice = v;
  }
  window.speechSynthesis.speak(u);
}

export function listVoices() {
  return hasSpeechSynthesis ? window.speechSynthesis.getVoices() : [];
}
