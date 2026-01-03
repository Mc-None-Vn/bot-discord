import pathlib, shutil
from data import data


ROOT = pathlib.Path(__file__).parent
SOURCES = {
    "commands": ROOT / "commands",
    "interactions": ROOT / "interactions",
}
PUBLIC = ROOT / "public"


def build_folder(src: pathlib.Path, dst: pathlib.Path):
    if not src.exists():
        return

    dst.mkdir(parents=True, exist_ok=True)
    for file in src.rglob("*"):
        if file.is_dir():
            continue

        rel = file.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Skipping {file}, not UTF-8")
            continue
        out.write_text(data(text), encoding="utf-8")


def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, src in SOURCES.items():
        build_folder(src, PUBLIC / name)
    shutil.copy2(ROOT / "data.json", PUBLIC / "data.json")


if __name__ == "__main__":
    main()
