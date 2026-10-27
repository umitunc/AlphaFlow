# -*- coding: utf-8 -*-
"""
JSON tabanlı çoklu dil (TR / EN) yöneticisi.
İşletim sistemi dili Türkçe ise `assets/i18n/tr.json`, değilse `assets/i18n/en.json` yükler.
"""

import ctypes
import json
import locale
import os
from pathlib import Path
from typing import Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]


def detect_os_lang_code() -> str:
    """İşletim sistemi dilini tespit eder: Türkçe ise 'tr', değilse 'en' döner."""
    try:
        if os.name == "nt":
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            # 0x041F (1055) = tr-TR, birincil dil kodu 0x1F = Türkçe
            if (lang_id & 0x3FF) == 0x1F:
                return "tr"
        loc = (locale.getlocale()[0] or os.environ.get("LANG", "")).lower()
        if loc.startswith("tr") or "turkish" in loc:
            return "tr"
    except Exception:
        pass
    return "en"


class JsonI18n:
    def __init__(self, lang_code: Optional[str] = None) -> None:
        self.lang_code = lang_code or detect_os_lang_code()
        self._strings: Dict[str, str] = {}
        self.load(self.lang_code)

    def load(self, lang_code: str) -> None:
        self.lang_code = "tr" if lang_code.lower().startswith("tr") else "en"
        json_path = ROOT_DIR / "assets" / "i18n" / f"{self.lang_code}.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._strings = {str(k): str(v) for k, v in data.items()}

    def t(self, key: str, **kwargs: object) -> str:
        val = self._strings.get(key, key)
        for k, v in kwargs.items():
            val = val.replace(f"{{{k}}}", str(v))
        return val


i18n = JsonI18n()
