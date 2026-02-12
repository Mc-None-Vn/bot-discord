import pathlib, shutil, os, json
from pymongo import MongoClient
from data import replaceText


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
        out.write_text(replaceText(text), encoding="utf-8")


def fetch_data_json_from_mongo():
    url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("MONGO_DB")
    col_name = os.environ.get("MONGO_COLLECTION")

    if not all([url, db_name, col_name]):
        print("Mongo ENV missing, skip data.json build")
        return

    try:
        client = MongoClient(url)
        col = client[db_name][col_name]
        docs = col.find()
        result = {}
        
        for doc in docs:
            key = doc.get("_id")
            if not key:
                continue
            doc.pop("_id", None)
            result[key] = doc

        out = PUBLIC / "data.json"
        out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("Built data.json from Mongo")
    except Exception as e:
        print("Mongo fetch failed:", e)


def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    fetch_data_json_from_mongo()
    for name, src in SOURCES.items():
        build_folder(src, PUBLIC / name)


if __name__ == "__main__":
    main()
