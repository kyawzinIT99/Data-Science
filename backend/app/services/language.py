"""Language detection and multi-language analysis support."""

from langdetect import detect, detect_langs, LangDetectException

LANGUAGE_NAMES = {
    "en": "English", "ar": "Arabic", "fr": "French", "es": "Spanish",
    "de": "German", "zh-cn": "Chinese", "zh-tw": "Chinese", "ja": "Japanese",
    "ko": "Korean", "pt": "Portuguese", "ru": "Russian", "it": "Italian",
    "nl": "Dutch", "tr": "Turkish", "hi": "Hindi", "th": "Thai",
    "vi": "Vietnamese", "pl": "Polish", "sv": "Swedish", "da": "Danish",
    "no": "Norwegian", "fi": "Finnish", "id": "Indonesian", "ms": "Malay",
    "my": "Myanmar",
}


def detect_language(text: str) -> tuple[str, float]:
    """Detect the language of text. Returns (lang_code, confidence)."""
    try:
        sample = text[:5000]
        langs = detect_langs(sample)
        if langs:
            top = langs[0]
            return str(top.lang), round(top.prob, 3)
    except LangDetectException:
        pass
    return "en", 1.0


def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code.upper())


def get_analysis_system_prompt(lang_code: str, custom_role: str = "data analyst") -> str:
    """Get a system prompt that instructs the AI to respond in the detected language."""
    lang_name = get_language_name(lang_code)
    if lang_code == "en":
        return f"You are a {custom_role}. Provide accurate, insightful analysis. Return valid JSON only."
    return (
        f"You are a {custom_role}. The document is in {lang_name}. "
        f"Provide your analysis in {lang_name}. "
        f"Return valid JSON only, with all text values in {lang_name}."
    )


def get_chat_system_prompt(lang_code: str, context: str) -> str:
    lang_name = get_language_name(lang_code)
    base = (
        "You are an AI assistant that answers questions based on the provided document context. "
        "Use the context below to answer accurately. If the answer is not in the context, say so clearly. "
        "If the user asks for a forecast or prediction of future prices, you MUST use the available tools to generate it. "
        "Be concise but thorough."
    )
    if lang_code != "en":
        base += f"\n\nIMPORTANT: The document is in {lang_name}. Respond in {lang_name}."
    return f"{base}\n\nDocument Context:\n{context}"
