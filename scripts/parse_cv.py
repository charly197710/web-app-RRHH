import sys, json, pathlib, subprocess, tempfile, os
from pdfminer.high_level import extract_text as extract_pdf
try:
    from docx import Document
    HAS_DOCX = True
except Exception:
    HAS_DOCX = False

def extract_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def process_file(path):
    text = ""
    if path.suffix.lower() == ".pdf":
        text = extract_pdf(str(path))
    elif path.suffix.lower() in [".docx", ".doc"]:
        if HAS_DOCX:
            text = extract_docx(path)
        else:
            # fallback anti-word
            result = subprocess.run(["antiword", str(path)], capture_output=True, text=True)
            text = result.stdout
    else:
        text = path.read_text(errors="ignore")
    return text.strip()

def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("./cvs")
    dst = pathlib.Path("./parsed")
    dst.mkdir(parents=True, exist_ok=True)
    for file in src.rglob("*"):
        if file.is_file() and file.suffix.lower() in [".pdf", ".docx", ".doc", ".txt"]:
            txt = process_file(file)
            out = dst / (file.stem + ".json")
            out.write_text(json.dumps({"filename": file.name, "text": txt}, ensure_ascii=False, indent=2))
            print(f"Procesado: {file.name}")

if __name__ == "__main__":
    main()