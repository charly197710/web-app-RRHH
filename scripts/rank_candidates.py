import json, pathlib, csv, sys

def main():
    # Determinar fuente de datos
    src_arg = sys.argv[1] if len(sys.argv) > 1 else "./scored"
    source = pathlib.Path(src_arg)
    # Si el usuario especificó --source en la llamada desde el skill, lo manejamos en el wrapper
    # Pero aquí aceptamos directamente la ruta.
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    out_csv = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("./top_candidates.csv")
    # Detectar si es detailed buscando breakdown en alguno de los jsons
    sample_file = next(source.rglob("*.json"), None)
    detailed = False
    if sample_file:
        try:
            data = json.loads(sample_file.read_text(encoding="utf-8"))
            if "breakdown" in data:
                detailed = True
        except Exception:
            pass

    records = []
    for js in source.rglob("*.json"):
        data = json.loads(js.read_text(encoding="utf-8"))
        record = {
            "filename": data.get("filename"),
            "score": data.get("score", 0),
        }
        if detailed:
            # Añadir columnas de cada criterio con puntos obtenidos
            breakdown = data.get("breakdown", {})
            for crit, info in breakdown.items():
                record[f"{crit}_earned"] = info.get("earned", 0)
                record[f"{crit}_weight"] = info.get("weight", 0)
        # Preview de texto (opcional)
        record[\"text_preview\"] = data.get(\"text\", \"\")[:200].replace(\"\\n\", \" \")
        records.append(record)

    records.sort(key=lambda x: x[\"score\"], reverse=True)
    top = records[:top_n]

    # Determinar encabezados CSV
    if detailed:
        # собрать все уникальные колонки кроме filename, score, text_preview
        extra_keys = set()
        for r in records:
            for k in r:
                if k not in (\"filename\", \"score\", \"text_preview\"):
                    extra_keys.add(k)
        fieldnames = [\"filename\", \"score\"] + sorted(extra_keys) + [\"text_preview\"]\n    else:\n        fieldnames = [\"filename\", \"score\", \"text_preview\"]\n\n    # escribe CSV\n    with out_csv.open(\"w\", newline=\"\", encoding=\"utf-8\") as f:\n        writer = csv.DictWriter(f, fieldnames=fieldnames)\n        writer.writeheader()\n        writer.writerows(top)\n\n    # imprime tabla simple\n    print(f\"Top {len(top)} candidatos:\")\n    # encabezado simplificado\n    header = f\"{'filename':30} | {'score':5}\"\n    if detailed:\n        header += \" | \" + \" | \".join([f\"{k[:8]:>8}\" for k in sorted(extra_keys)])\n    print(header)\n    print(\"-\" * len(header))\n    for r in top:\n        line = f\"{r.get('filename',''):30} | {r.get('score',0):5}\"\n    if detailed:\n        vals = []\n        for k in sorted(extra_keys):\n            vals.append(str(r.get(k,0)).rjust(8))\n        line += \" | \" + \" \\\".join(vals)\n    print(line)\n    print(f\"\\nCSV guardado en: {out_csv}\")\n\nif __name__ == \"__main__\":\n    main()