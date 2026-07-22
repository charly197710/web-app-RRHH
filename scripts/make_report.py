import csv, pathlib, sys, json

def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("./top_candidates.csv")
    fmt = sys.argv[2] if len(sys.argv) > 2 else "csv"
    dest = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("./reporte.txt")
    detailed = False
    # Detectar si el CSV contiene columnas de detalle (contienen '_earned' o '_weight')
    if src.exists():
        try:
            with src.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                if any("_earned" in f or "_weight" in f for f in fieldnames):
                    detailed = True
        except Exception:
            pass

    if fmt == "csv":
        dest.write_bytes(src.read_bytes())
        print(f"CSV copiado a {dest}")
        return

    # generar reporte TXT
    lines = ["=== Reporte de Candidatos ==="]
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lines.append(f"{row.get('filename','')} - Puntaje: {row.get('score','0')}")
            if detailed:
                # mostrar desglose
                earned_items = [(k.replace('_earned',''), v) for k, v in row.items() if k.endswith('_earned') and v.isdigit() and int(v) > 0]
                if earned_items:
                    detalle = ", ".join([f"{name}:{pts}" for name, pts in earned_items])
                    lines.append(f"  Detalle (puntos obtenidos): {detalle}")
            lines.append(f"  Preview: {row.get('text_preview','')}")
            lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"Reporte TXT generado en {dest}")

if __name__ == "__main__":
    main()