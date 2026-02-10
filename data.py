from functools import lru_cache
import os, json, re


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


_EMOJI_RE = re.compile(r"\{emoji:([\w\.]+)\}")
_DATA_RE  = re.compile(r"\{data:([\w\.]+)\}")
_COUNT_RE  = re.compile(r"\{count(\d+)?\}")
_REPEAT_RE = re.compile(r"\{repeat(\d+):(.+?)\}", re.DOTALL)

def _apply_count(content: str, i: int):
    def repl(m):
        start = int(m.group(1)) if m.group(1) else 0
        return str(start + i)
    return _COUNT_RE.sub(repl, content)

def replaceText(text: str) -> str:
    data_json = _load_data_json()
    text = text.replace(r'\}', '%RB%')

    def repl_emoji(m):
        val = _get_by_path(data_json.get("e", {}), m.group(1))
        return str(val) if val is not None else m.group(0)

    def repl_data(m):
        val = _get_by_path(data_json.get("bdfd", {}), m.group(1))
        return str(val) if val is not None else m.group(0)

    def repl_repeat(m):
        times = int(m.group(1))
        content = m.group(2)
        result = ''
        for i in range(0, times):
            part = _apply_count(content, i)
            result += part
        return result

    text = _EMOJI_RE.sub(repl_emoji, text)
    text = _DATA_RE.sub(repl_data, text)
    text = _REPEAT_RE.sub(repl_repeat, text)
    text = text.replace('%RB%', '}')
    return text
