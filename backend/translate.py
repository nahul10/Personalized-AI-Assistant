from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# fast and good for many directions:
_MODEL = "facebook/nllb-200-distilled-600M"
_tok, _mt = None, None

def _ensure():
    global _tok,_mt
    if _tok is None:
        _tok = AutoTokenizer.from_pretrained(_MODEL)
        _mt  = AutoModelForSeq2SeqLM.from_pretrained(_MODEL)

def translate(text: str, tgt_lang: str) -> str:
    lang_map = {"tamil":"tam_Taml","ta":"tam_Taml","french":"fra_Latn","fr":"fra_Latn"}
    code = lang_map.get(tgt_lang.lower(), "eng_Latn")
    _ensure()
    inp = _tok(text, return_tensors="pt")
    gen = _mt.generate(**inp, forced_bos_token_id=_tok.lang_code_to_id[code], max_new_tokens=512)
    return _tok.decode(gen[0], skip_special_tokens=True)
