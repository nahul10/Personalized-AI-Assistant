export function speak(text, voice = "auto") {
  if (!window.speechSynthesis) return;

  const msg = new SpeechSynthesisUtterance(text);
  if (voice === "male") {
    msg.voice = speechSynthesis.getVoices().find(v => v.name.includes("Male")) || null;
  } else if (voice === "female") {
    msg.voice = speechSynthesis.getVoices().find(v => v.name.includes("Female")) || null;
  }
  window.speechSynthesis.speak(msg);
}
