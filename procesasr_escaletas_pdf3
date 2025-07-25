import pdfplumber
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# CONFIGURACIÓN
CARPETA_PDFS = "escaletas_pdf"
SHEET_DISCOS = "Discos Empleados"
SHEET_DESTINO = "Escaletas Empleados"

# --- Funciones auxiliares ---
def romano_a_arabigo(s):
    romanos = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
    s = s.upper()
    total = 0
    prev = 0
    for c in reversed(s):
        valor = romanos.get(c, 0)
        if valor < prev:
            total -= valor
        else:
            total += valor
            prev = valor
    return total

def autenticar_google():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    return gspread.authorize(creds)

def obtener_diccionario_discos(client):
    hoja = client.open(SHEET_DISCOS).sheet1
    datos = hoja.get_all_records()
    return { (int(f['Temporada']), int(f['Programa'])): f['Disco'] for f in datos if f.get('Temporada') and f.get('Programa') }

def extraer_temporada_programa_fecha(texto):
    temporada = programa = 0
    fecha = ""
    # PROGRAMA X-YY
    m = re.search(r'PROGRAMA\s*(\d+)\s*[-–]\s*([A-Z\d]+)', texto, re.IGNORECASE)
    if m:
        programa = int(m.group(1))
        tmp = m.group(2)
        temporada = int(tmp) if tmp.isdigit() else romano_a_arabigo(tmp)

    # Emisión: fecha con /, -, espacios, mes numérico o nombre (ene, enero, etc), año de 2 o 4 dígitos
    meses = {
        'enero':1, 'ene':1, 'febrero':2, 'feb':2, 'marzo':3, 'mar':3, 'abril':4, 'abr':4,
        'mayo':5, 'may':5, 'junio':6, 'jun':6, 'julio':7, 'jul':7, 'agosto':8, 'ago':8,
        'septiembre':9, 'sep':9, 'setiembre':9, 'set':9, 'octubre':10, 'oct':10,
        'noviembre':11, 'nov':11, 'diciembre':12, 'dic':12
    }
    # Busca: Emisión: 1/ene/22, 1-ene-22, 1 enero 22, etc
    m2 = re.search(r'[EeÉé]misi[oó]n[:：]?\s*(\d{1,2})\s*([/\-\s])\s*([A-Za-záéíóúñÑ]+|\d{1,2})\s*\2\s*(\d{2,4})', texto)
    if m2:
        dia, mes_raw, anio = m2.group(1), m2.group(3), m2.group(4)
        # Convertir mes a número si es texto
        if mes_raw.isdigit():
            mes = int(mes_raw)
        else:
            mes = meses.get(mes_raw.strip().lower(), 0)
        # Normalizar año a 4 dígitos si es necesario
        if len(anio) == 2:
            anio = '20' + anio if int(anio) < 50 else '19' + anio
        fecha = f"{int(dia):02d}/{int(mes):02d}/{anio}" if mes else ""

    return temporada, programa, fecha

def limpiar_seccion(s):
    return re.sub(r'^V[IÍ]DEO\s*\d+\.\s*', '', s, flags=re.IGNORECASE).strip()

def extraer_reportajes_pdf(path_pdf):
    # 1) Leemos todo el texto para encabezado
    texto_enc = ""
    with pdfplumber.open(path_pdf) as pdf:
        for pg in pdf.pages:
            txt = pg.extract_text() or ""
            texto_enc += txt + "\n"
    temporada, programa, fecha = extraer_temporada_programa_fecha(texto_enc)

    reportajes = []
    # 2) Ahora línea a línea
    with pdfplumber.open(path_pdf) as pdf:
        for pg in pdf.pages:
            lines = (pg.extract_text() or "").split("\n")
            for linea in lines:
                linea = linea.strip()
                # comienza con número de reportaje
                if not re.match(r'^\d+\s+', linea):
                    continue
                partes = linea.split()
                if len(partes) < 4:
                    continue

                # número y presentador
                num = partes[0]
                presentador = partes[1]

                # buscar duración (primer token mm:ss)
                dur = ""
                idx_dur = None
                for i, tok in enumerate(partes[2:], start=2):
                    if re.fullmatch(r'\d{1,2}:\d{2}', tok):
                        dur, idx_dur = tok, i
                        break
                if idx_dur is None:
                    continue  # sin duración válida

                # sección = de partes[2] hasta idx_dur-1
                seccion_raw = " ".join(partes[2:idx_dur])
                seccion = limpiar_seccion(seccion_raw)

                # ciudad = resto de tokens tras duración (puede quedar vacío)
                ciudad = " ".join(partes[idx_dur+1:]).strip()

                reportajes.append({
                    "Temporada": temporada,
                    "Programa": programa,
                    "Fecha": fecha,
                    "Presentador": presentador,
                    "Seccion": seccion,
                    "Duracion": dur,
                    "Ciudad": ciudad
                })
    return reportajes

def subir_a_sheets(client, datos, discos):
    sheet = client.open(SHEET_DESTINO).sheet1
    # Obtener número de filas actuales para saber dónde empezar a escribir
    num_filas = len(sheet.get_all_values())
    # Si la hoja está vacía, agregar cabecera
    if num_filas == 0:
        sheet.append_row(['Temporada','Programa','Fecha','Presentador','Seccion','Duracion','Ciudad','Disco'])
    filas = []
    sin_disco = 0
    for r in datos:
        clave = (r['Temporada'], r['Programa'])
        disco = discos.get(clave, "No encontrado")
        if disco == "No encontrado":
            sin_disco += 1
        filas.append([
            r['Temporada'], r['Programa'], r['Fecha'],
            r['Presentador'], r['Seccion'],
            r['Duracion'], r['Ciudad'], disco
        ])
    if filas:
        sheet.append_rows(filas)
    print(f"Total reportajes: {len(datos)}, sin disco: {sin_disco}")

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    client = autenticar_google()
    discos = obtener_diccionario_discos(client)
    todos = []
    for f in os.listdir(CARPETA_PDFS):
        if f.lower().endswith(".pdf"):
            path = os.path.join(CARPETA_PDFS, f)
            rpt = extraer_reportajes_pdf(path)
            todos.extend(rpt)
            print(f"{f}: {len(rpt)} reportajes")
    subir_a_sheets(client, todos, discos)
