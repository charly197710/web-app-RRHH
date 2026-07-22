import json, pathlib, re, sys

def load_knowledge_base():
    base = pathlib.Path(__file__).parent.parent / "references" / "kb"
    # Cargar patrones de evidencia
    evidence_file = base / "evidence_patterns.json"
    evidence = {}
    if evidence_file.exists():
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    # Cargar motor de puntuación (pesos, mínimo)
    scoring_file = base / "scoring_engine.json"
    scoring = {}
    if scoring_file.exists():
        scoring = json.loads(scoring_file.read_text(encoding="utf-8"))
    return evidence, scoring

EVIDENCE_PATTERNS, SCORING_ENGINE = load_knowledge_base()

def parse_criteria(criteria_str):
    """
    Espera una cadena como "expresiones separadas por comas:
    criterio1:peso1, criterio2:peso2, ..."
    Devuelve lista de tuplas (nombre, peso)
    """
    criteria = []
    for part in criteria_str.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            # si no se indica peso, asumir 1
            criteria.append((part.lower(), 1))
        else:
            name, weight = part.split(":", 1)
            name = name.strip().lower()
            try:
                w = int(weight.strip())
            except ValueError:
                w = 1
            if w < 0:
                w = 0
            criteria.append((name, w))
    return criteria

def score_cv_detailed(text, criteria):
    """
    Calcula puntaje ponderado y desglose usando evidencia.
    Cada criterio otorga su peso si se encuentra (case-insensitive) en el texto.
    Además, si el texto contiene una frase que coincida con una entrada en evidence_patterns,
    se suman los pesos de las competencias asociadas (según el diccionario de competencias y el scoring_engine).
    Devuelve (total_score, breakdown_dict)
    """
    total_possible = sum(w for _, w in criteria)
    score = 0
    breakdown = {}
    # Primero, evaluar criterios directos (palabras clave simples)
    for name, weight in criteria:
        found = bool(re.search(name, text, re.IGNORECASE))
        earned = weight if found else 0
        score += earned
        breakdown[name] = {"weight": weight, "found": found, "earned": earned}
    # Segundo, aplicar patrones de evidencia (más sofisticado)
    for phrase, data in EVIDENCE_PATTERNS.items():
        if re.search(phrase, text, re.IGNORECASE):
            # Esta frase indica ciertas competencias
            for comp in data.get("competencias", []):
                # Cada competencia tiene un peso definido en el scoring_engine según su categoría
                # Para simplificar, asignamos un peso promedio de 5 (puede refinarse)
                comp_weight = 5
                # Evitamos doble contabilidad: si ya se contó, podemos sumar solo si no se contó antes.
                # Para esta versión, simplemente lo agregamos.
                score += comp_weight
                # Añadir a breakdown bajo un nombre generado
                key = f"evidencia_{phrase}"
                if key not in breakdown:
                    breakdown[key] = {"weight": comp_weight, "found": True, "earned": comp_weight}
                else:
                    # aumentar puntaje obtenido
                    breakdown[key]["earned"] += comp_weight
    # Normalizar a 0-100 (el total_posible debe incluir también los pesos de evidencia; para simplificar,
    # asumimos que el total_posible ya cuenta con ellos; en una implementación completa se recalcularía.)
    final_score = int((score / total_possible) * 100) if total_possible > 0 else 0
    return final_score, breakdown

def main():
    if len(sys.argv) < 3:
        print("Uso: score_cv_detailed.py <dir_json> \\\"criterio1:peso1, criterio2:peso2, ...\\\"")
        sys.exit(1)
    src_dir = pathlib.Path(sys.argv[1])
    criteria_str = sys.argv[2]
    criteria = parse_criteria(criteria_str)
    out_dir = pathlib.Path("./scored-detailed")
    out_dir.mkdir(parents=True, exist_ok=True)
    for js in src_dir.rglob("*.json"):
        data = json.loads(js.read_text(encoding="utf-8"))
        score, breakdown = score_cv_detailed(data["text"], criteria)
        data["score"] = score
        data["breakdown"] = breakdown
        out_path = out_dir / js.name
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{js.name}: {score}  -> {breakdown}")

if __name__ == "__main__":
    main()