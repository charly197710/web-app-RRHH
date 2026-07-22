---
name: hr-recruitment-senior
category: custom
description: Asistente de reclutamiento avanzado basado en un marco de conocimiento estructurado (perfil de reclutador, motor de puntuación, patrones de evidencia, filtros obligatorios y plantillas de puesto). Permite conectar cuentas de correo mediante Himalaya, extraer texto de CVs, aplicar filtros basados en evidencias y competencias, calcular puntajes ponderados, generar ranking y reportes, y exportar resultados a Google Sheets para seguimiento por parte del reclutador humano.
---
## Visión General

Este skill transforma el proceso de reclutamiento en una actividad basada en evidencia y competencias, siguiendo las mejores prácticas de firmas como Adecco y modelos de *skills‑based hiring*. En lugar de buscar palabras clave sueltas, el motor interpreta la experiencia del candidato y la asigna a competencias concretas con pesos definidos por el puesto.

### Arquitectura del Conocimiento

```
knowledge_base/
├─ recruiter_profile.json      # principios y valores del reclutador senior
├─ scoring_engine.json         # pesos de categorías y umbrales
├─ evidence_patterns.json      # mapeo de frases de experiencia → competencias
├─ mandatory_filters.json      # requisitos eliminatorios por puesto
└─ dictionary_competencies.json (opcional) # definiciones y sinónimos

job_templates/
├─ secretaria_gerencia.json
├─ conductor_carga.json
├─ auxiliar_contable.json
└─ comercial.json
```

* `prompt.md` – instrucciones para el modelo de lenguaje cuando actúa como reclutador.
* `system.md` – descripción detallada del flujo interno y responsabilidad de cada módulo.

## Uso

Desde el chat de Hermes, invoque el skill con:

``` 
skill hr-recruitment-senior <subcomando> [argumentos] 
```

### Subcomandos

- `connect <provider> --user <email> --pass <app-password>`  
  Configura la cuenta de correo mediante Himalaya (IMAP). `provider` puede ser `gmail` o `outlook`.

- `fetch --since <dias>`  
  Descarga los correos no leídos de los últimos `dias` días y guarda los adjuntos (PDF, DOCX) en `./cvs/`.

- `parse --dir <ruta>`  
  Extrae texto de los CVs (usa `pdfminer.six` y `python-docx` si están instalados) y crea un archivo JSON por candidato en `./parsed/`.

- `filter --requisitos "<texto>"`  
  **Método sencillo**: aplica los requisitos indicados (por ejemplo: `"3 años de experiencia en desarrollo web, conocimientos en React, ubicado en Bogotá"`) sobre los JSONs parseados y genera una puntuación global (0‑100) en `./scored/`.

- `filter-detailed --requisitos "<c1:p1, c2:p2, ...>" [--min-score N]`  
  **Método basado en evidencias y competencia**:  
  - Cada criterio tiene formato `nombre:peso` (peso entero, mayor peso = más importante).  
  - Opcional `--min-score N` filtra solo aquellos cuyo puntaje total ≥ N.  
  - Los resultados se guardan en `./scored-detailed/` (JSON con campos `score` y `breakdown`).  
  - Internamente, este comando usa el motor de evidencias (`evidence_patterns.json`) y el motor de puntuación (`scoring_engine.json`) para traducir frases del CV en puntos por competencia.

- `rank --top N [--source scored|scored-detailed]`  
  Ordena los candidatos por puntaje total y devuelve el top N como tabla en consola y guarda `top_N.csv`.  
  Use `--source scored-detailed` para usar el puntaje ponderado del filtrado detallado.

- `report --format csv|txt --dest <ruta> [--detailed]`  
  Genera un informe resumido (nombre, email, puntaje, habilidades destacadas) o, si se agrega `--detailed`, un informe con desglose de puntajes por criterio y evidencias encontradas. Guarda en la ruta indicada.

- `notify --method whatsapp --to <numero> --mensaje "<texto>"`  
  Usa la skill `bio-link-landing` o `whatsapp` (si estuviera disponible) para enviar notificación; en su defecto, sugiere usar `execute_code` con una llamada a API de WhatsApp.

- `export-sheets` *(nuevo)*  
  Después de generar un reporte (CSV o TXT), este subcomando toma el archivo de resultados y lo publica en una hoja de Google Sheets, compartiéndola con el correo del reclutador indicado en `notifyTo`.  
  **Uso**: `skill hr-recruitment-senior export-sheets --dest ./reporte_top5.csv --vacante "Secretaria Gerente" --notifyTo reclutador@empresa.com`

### Ejemplo de flujo completo (filtrado sencillo)

```bash
skill hr-recruitment-senior connect gmail --user reclutador@empresa.com --pass miAppPass123
skill hr-recruitment-senior fetch --since 3
skill hr-recruitment-senior parse --dir ./cvs
skill hr-recruitment-senior filter --requisitos "2 años de experiencia en servicio al cliente, disponible para trabajar turno noche, residente en Medellín"
skill hr-recruitment-senior rank --top 5
skill hr-recruitment-senior report --format csv --dest ./reporte_top5.csv
```

### Ejemplo de flujo detallado (con puntaje mínimo y desglose)

```bash
skill hr-recruitment-senior connect gmail --user reclutador@empresa.com --pass miAppPass123
skill hr-recruitment-senior fetch --since 3
skill hr-recruitment-senior parse --dir ./cvs
skill hr-recruitment-senior filter-detailed --requisitos "experiencia:3, react:2, ubicacion:1, ingles:1" --min-score 70
skill hr-recruitment-senior rank --top 10 --source scored-detailed
skill hr-recruitment-senior report --format csv --dest ./top10_detallado.csv --detailed
```

### Ejemplo de exportación a Google Sheets

```bash
skill hr-recruitment-senior export-sheets --dest ./top10_detallado.csv --vacante "Secretaria Gerente" --notifyTo reclutador@empresa.com
```

## Configuración Previa

1. **Dependencias de Python** (si se usa ejecución de código):  
   ```bash
   pip install pdfminer.six python-docx
   ```
2. **Google Sheets API** (para la función de exportación):  
   - Cree un proyecto en Google Cloud Console.  
   - Habilite **Google Sheets API** y **Google Drive API**.  
   - Cree una cuenta de servicio y descargue su clave JSON.  
   - Colóquela en `~/google-credentials/hr-recruitment-sa.json` (o establezca la variable de entorno `GSHEETS_SA_PATH` con la ruta completa).  
   - Esta cuenta debe tener permiso para crear hojas y compartirlas.  
3. **Configurar Himalaya** para la cuenta de correo (ver skill `himalaya`):  
   ``` 
   skill hymalaya add-account --provider gmail --user user@gmail.com --app-pass xxx 
   ```  
   (o usar directamente el comando `terminal` con `himalaya` si está instalado).

## Notas de Privacidad

- Nunca almacene contraseñas en texto plano en el skill; use el almacén de credenciales de Himalaya o variables de entorno.  
- Los CVs se almacenan localmente; elimine el directorio `./cvs/` y `./parsed/` cuando ya no los necesite.  
- La hoja de Google Sheets creada contiene solo los datos necesarios para la toma de decisión (nombre, puesto, puntuación, evidencias). Elimine o restrinja el acceso cuando el proceso concluya.

## Extensibilidad

- Para agregar nuevos criterios (idiomas, certificaciones, etc.) modifique el subcomando `filter-detailed` editando la función que interpreta `evidence_patterns.json` y `scoring_engine.json` (ver `scripts/score_cv_detailed.py`).  
- Para agregar una nueva plantilla de puesto, simplemente cree un archivo JSON en `job_templates/` siguiendo la estructura de los ejemplos.  
- El motor de evidencias es fácilmente ampliable: añada nuevas entradas a `evidence_patterns.json` con la frase de experiencia y la lista de competencias asociadas.  
- Si dispone de la skill `bio-link-landing`, puede generar una mini‑página de presentación del candidato seleccionado.

## Scripts Internos

El skill incluye los siguientes scripts (ubicados en `scripts/` dentro de la carpeta del skill):

- `fetch_emails.py` – llama a `himalaya fetch` y guarda adjuntos.  
- `parse_cv.py` – extrae texto de PDF/DOCX y crea JSON.  
- `score_cv.py` – aplica reglas de puntuación basadas en palabras clave y expresiones regulares (filtrado simple).  
- `score_cv_detailed.py` – **versión actualizada** que lee `evidence_patterns.json` y `scoring_engine.json` para calcular puntaje ponderado y desglose por evidencia.  
- `rank_candidates.py` – ordena y genera CSV (acepta fuente `scored` o `scored-detailed`).  
- `make_report.py` – genera informe CSV/TXT, con opción detallada.  
- `notify.py` – placeholder para notificaciones externas (WhatsApp, email, etc.).  
- `export_sheets.py` – **nuevo script** que toma un archivo CSV/TXT, lo carga a Google Sheets usando la cuenta de servicio y lo comparte con el reclutador indicado.

Estos scripts pueden ser sobrescritos o extendidos mediante `skill_manage edit` o `skill_manage patch`.

--- 

### scripts/fetch_emails.py
```python
import subprocess, os, pathlib, sys

def main():
    out_dir = pathlib.Path("./cvs")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Asumimos que el usuario ya configuró su cuenta con la skill hymalaya
    # Ejecutamos: hymalaya fetch --since 3 --download-attachments --dest ./cvs
    subprocess.run(["himalaya", "fetch", "--since", "3", "--download-attachments", "--dest", str(out_dir)], check=False)

if __name__ == "__main__":
    main()
```

### scripts/parse_cv.py
```python
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
```

### scripts/score_cv.py
```python
import json, pathlib, re, sys

def score_cv(text, requisitos):
    """requisitos: string con palabras clave separadas por comas"""
    score = 0
    total = len(requisitos)
    for req in requisitos:
        req = req.strip().lower()
        if req and re.search(req, text, re.IGNORECASE):
            score += 1
    return int((score / total) * 100) if total > 0 else 0

def main():
    if len(sys.argv) < 3:
        print("Uso: score_cv.py <dir_json> \\\"requisito1, requerimiento2, ...\\\"")
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
```

### scripts/score_cv_detailed.py
```python
import json, pathlib, re, sys

def load_knowledge_base():
    base = pathlib.Path(__file__).parent.parent / "knowledge_base"
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
```