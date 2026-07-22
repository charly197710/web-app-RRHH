import os, csv, pathlib, sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Ruta a la cuenta de servicio (se puede sobrescribir con variable de entorno GSHEETS_SA_PATH)
SERVICE_ACCOUNT_FILE = os.getenv(
    "GSHEETS_SA_PATH",
    os.path.join(os.path.expanduser("~"), "google-credentials", "hr-recruitment-sa.json")
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

def _get_client():
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def _get_drive_service():
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds, cache_discovery=False)

def _read_csv_to_rows(csv_path):
    """Devuelve lista de listas (filas) incluyendo encabezado."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return [row for row in reader]

def export_to_sheet(csv_path, spreadsheet_title, worksheet_name="Hoja1", share_with=None):
    """
    Crea (o reutiliza) una hoja de cálculo con el título indicado,
    escribe los datos del CSV en la hoja de trabajo indicada y,
    si se proporciona `share_with`, la comparte con ese correo como escritor.
    Devuelve la URL de la hoja.
    """
    sheets_service = _get_client()
    drive_service = _get_drive_service()

    # Intentar abrir hoja existente; si no existe, crearla
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            ranges=[spreadsheet_title]
        ).execute()
    except Exception:
        # Crear nueva hoja
        spreadsheet_body = {
            "properties": {"title": spreadsheet_title}
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
    spreadsheet_id = spreadsheet.get("spreadsheetId")

    # Asegurar que exista la hoja de trabajo (worksheet)
    sheets = spreadsheet.get("sheets", [])
    sheet_titles = [s["properties"]["title"] for s in sheets]
    if worksheet_name not in sheet_titles:
        # Añadir hoja
        add_sheet_body = {
            "requests": [{
                "addSheet": {
                    "properties": {
                        "title": worksheet_name,
                        "gridProperties": {
                            "rowCount": 1000,
                            "columnCount": 20
                        }
                    }
                }
            }]
        }
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=add_sheet_body
        ).execute()

    # Leer CSV y actualizar hoja
    rows = _read_csv_to_rows(csv_path)
    body = {
        "valueInputOption": "RAW",
        "data": [{
            "range": f"{worksheet_name}!A1",
            "majorDimension": "ROWS",
            "values": rows
        }]
    }
    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    # Opcional: compartir con el reclutador
    if share_with:
        permission_body = {
            "type": "user",
            "role": "writer",
            "emailAddress": share_with
        }
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission_body,
            fields="id"
        ).execute()

    # Construir URL de visualización
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return url

def main():
    if len(sys.argv) < 4:
        print("Uso: export_sheets.py <csv_path> --vacante <titulo> --notifyTo <email>")
        sys.exit(1)
    csv_path = sys.argv[1]
    # parsear argumentos simples
    vacante = ""
    notify_to = ""
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--vacante" and i + 1 < len(sys.argv):
            vacante = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--notifyTo" and i + 1 < len(sys.argv):
            notify_to = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    if not vacante:
        vacante = "Reporte de Candidatos"
    try:
        url = export_to_sheet(csv_path, spreadsheet_title=vacante, share_with=notify_to)
        print(f"Hoja de Google creada y compartida: {url}")
        sys.exit(0)
    except Exception as e:
        print(f"Error al exportar a Google Sheets: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()