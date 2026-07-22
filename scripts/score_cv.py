import json, pathlib, re, sys

def score_cv(text, requisitos):
    """requisitos: string with keywords separated by commas"""
    score = 0
    total = len(requisitos)
    for req in requisitos:
        req = req.strip().lower()
        if req and re.search(req, text, re.IGNORECASE):
            score += 1
    return int((score / total) * 100) if total > 0 else 0

def main():
    if len(sys.argv) < 3:
        print("Uso: score_cv.py <dir_json> \"requisito1, requisito2, ...\"")
        sys.exit(1)
    src_dir = pathlib.Path(sys.argv[1])
    req_str = sys.argv[2]
    requisitos = [r.strip() for r in req_str.split(",") if r.strip()]
    out_dir = pathlib.Path("./scored")
    out_dir.mkdir(parents=True, exist_ok=True)
    for js in src_dir.rglob("*.json"):
        data = json.loads(js.read_text(encoding="utf-8"))
        score = score_cv(data["text"], requisitos)
        data["score"] = score
        out_path = out_dir / js.name
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{js.name}: {score}")

if __name__ == "__main__":
    main()