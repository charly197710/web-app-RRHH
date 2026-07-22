from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import sys
from pathlib import Path
import csv

app = Flask(__name__, static_folder='static', template_folder='templates')

BASE_DIR = Path(__file__).parent
SKILL_SCRIPTS = BASE_DIR / "integrations" / "hr-recruitment-assistant" / "scripts"

def run_script(script_name, args=[]):
    script_path = SKILL_SCRIPTS / script_name
    if not script_path.is_file():
        return {"error": f"Script not found: {script_path}"}
    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        return {
            "output": output,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Script timed out."}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}

# Import Google Sheets helper
try:
    from gsheet_helper import write_dataframe_to_sheet, share_spreadsheet
    GSHEETS_AVAILABLE = True
except Exception as e:
    GSHEETS_AVAILABLE = False
    print(f"Google Sheets helper not available: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json(silent=True) or {}
    days = int(data.get("days", 3))
    res = run_script("fetch_emails.py", ["--since", str(days)])
    return jsonify(res)

@app.route("/api/parse", methods=["POST"])
def api_parse():
    res = run_script("parse_cv.py", [str(BASE_DIR / "cvs")])
    return jsonify(res)

@app.route("/api/filter", methods=["POST"])
def api_filter():
    data = request.get_json(silent=True) or {}
    req = data.get("requisitos", "")
    res = run_script("score_cv_detailed.py", [str(BASE_DIR / "parsed"), req])
    return jsonify(res)

@app.route("/api/rank", methods=["POST"])
def api_rank():
    data = request.get_json(silent=True) or {}
    top = int(data.get("top", 5))
    source = data.get("source", "scored-detailed")
    res = run_script("rank_candidates.py", [source, str(top)])
    return jsonify(res)

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(silent=True) or {}
    fmt = data.get("format", "txt")
    dest = data.get("dest", "./reporte.txt")
    source = data.get("source", "./top_candidates.csv")
    detailed = "--detailed" if data.get("detailed") else ""
    args = [source, fmt, dest]
    if detailed:
        args.insert(3, detailed)  # before dest
    res = run_script("make_report.py", args)
    if res.get("returncode") == 0 and os.path.isfile(dest):
        # Return file for download
        return send_file(dest, as_attachment=True)
    return jsonify(res)

@app.route("/api/notify", methods=["POST"])
def api_notify():
    if not GSHEETS_AVAILABLE:
        return jsonify({"error": "Google Sheets integration not configured."}), 500
    data = request.get_json(silent=True) or {}
    informe_path = data.get("dest", "./reporte.txt")
    formato = data.get("format", "txt")
    vacante = data.get("vacante", "Vacante sin nombre").strip()
    reclutador_email = data.get("notifyTo", "").strip()
    if not os.path.isfile(informe_path):
        return jsonify({"error": f"Informe not found: {informe_path}"}), 400
    if not reclutador_email:
        return jsonify({"error": "Missing recruiter email."}), 400
    # Load report into list of rows
    try:
        if formato == "csv":
            with open(informe_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        else:
            # Try tab-separated, then comma
            try:
                with open(informe_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t')
                    rows = list(reader)
            except Exception:
                with open(informe_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
    except Exception as e:
        return jsonify({"error": f"Cannot read report: {e}"}), 400
    if not rows:
        return jsonify({"error": "Report is empty."}), 400
    # Ensure we have a score column; we assume header row exists
    header = [h.strip().lower() for h in rows[0]]
    if "score" not in header:
        # Try to find a column containing 'score'
        score_idx = None
        for i, h in enumerate(header):
            if "score" in h:
                score_idx = i
                break
        if score_idx is None:
            return jsonify({"error": "Report missing score column."}), 400
        # rename header to 'score' for consistency
        rows[0][score_idx] = "score"
        header[score_idx] = "score"
    # Determine score column index
    score_col = header.index("score")
    # Convert score to float for sorting; handle non-numeric gracefully
    def try_float(val):
        try:
            return float(val)
        except:
            return float('-inf')
    # Sort rows (excluding header) by score descending
    sorted_rows = [rows[0]] + sorted(rows[1:], key=lambda r: try_float(r[score_col] if len(r) > score_col else ''), reverse=True)
    # Build final rows for Google Sheets (ensure all rows have same length)
    max_cols = max(len(r) for r in sorted_rows)
    normalized = []
    for r in sorted_rows:
        if len(r) < max_cols:
            r = r + [''] * (max_cols - len(r))
        normalized.append(r)
    hoja_titulo = f"Informe de Reclutamiento – {vacante}"
    try:
        hoja_url = write_dataframe_to_sheet(normalized, hoja_titulo, worksheet_name="Candidatos")
    except Exception as e:
        return jsonify({"error": f"Failed to write to Google Sheets: {e}"}), 500
    try:
        share_spreadsheet(hoja_url, reclutador_email, role="writer")
    except Exception as e:
        return jsonify({"error": f"Failed to share sheet: {e}"}), 500
    return jsonify({"output": f"Hoja de Google creada y compartida: {hoja_url}", "returncode": 0, "url": hoja_url})

if __name__ == "__main__":
    for folder in ["cvs", "parsed", "scored", "scored-detailed"]:
        (BASE_DIR / folder).mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
