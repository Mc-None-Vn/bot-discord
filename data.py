from functools import lru_cache
import os, json, re

# ------------------ LOAD DATA.JSON ------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
@lru_cache(maxsize=1)
def _load_data_json() -> dict:
    public_path = os.path.join(ROOT_DIR, "public", "data.json")
    local_path = os.path.join(ROOT_DIR, "data.json")
    path = public_path if os.path.isfile(public_path) else local_path
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_by_path(data: dict, path: str):
    cur = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


# ------------------ COUNT ------------------
_COUNT_RE = re.compile(r"\{count(\d+)?\}")

def _apply_count(text: str, i: int):
    def repl(m):
        start = int(m.group(1)) if m.group(1) else 0
        return str(start + i)
    return _COUNT_RE.sub(repl, text)


# ------------------ REPEAT ------------------
def _find_closing_brace(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

def _process_repeat(text: str):
    i = 0
    out = ""
    while i < len(text):
        if text.startswith("{repeat", i):
            j = i + 7
            while j < len(text) and text[j].isdigit():
                j += 1
            if j >= len(text) or text[j] != ":":
                out += text[i]
                i += 1
                continue

            times = int(text[i+7:j])
            start_content = j + 1
            end = _find_closing_brace(text, i)
            if end == -1:
                out += text[i]
                i += 1
                continue

            content = text[start_content:end]
            content = _process_repeat(content)
            for k in range(times):
                part = _apply_count(content, k)
                out += part
            i = end + 1
        else:
            out += text[i]
            i += 1
    return out


# ------------------ EMOJI / DATA ------------------
_EMOJI_RE = re.compile(r"\{emoji:([\w\.]+)\}")
_DATA_RE  = re.compile(r"\{data:([\w\.]+)\}")

def _replace_vars(text: str, data_json: dict):
    def repl_emoji(m):
        val = _get_by_path(data_json.get("e", {}), m.group(1))
        return str(val) if val is not None else m.group(0)

    def repl_data(m):
        val = _get_by_path(data_json.get("bdfd", {}), m.group(1))
        return str(val) if val is not None else m.group(0)

    text = _EMOJI_RE.sub(repl_emoji, text)
    text = _DATA_RE.sub(repl_data, text)
    return text


# ------------------ MAIN ------------------
def replaceText(text: str) -> str:
    data_json = _load_data_json()
    text = text.replace(r'\}', '%RB%')
    text = _process_repeat(text)
    text = _replace_vars(text, data_json)
    text = text.replace('%RB%', '}')
    return text
