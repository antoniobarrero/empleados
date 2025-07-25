import subprocess
import os

def doc_to_pdf(doc_path, output_dir=None, soffice_path="/Applications/LibreOffice.app/Contents/MacOS/soffice"):
    if output_dir is None:
        output_dir = os.path.dirname(doc_path)

    try:
        subprocess.run([
            soffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            doc_path
        ], check=True)
        print(f"Convertido: {doc_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error al convertir {doc_path}: {e}")

def convertir_carpeta_docs(folder_path, soffice_path="/Applications/LibreOffice.app/Contents/MacOS/soffice"):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".doc", ".docx")):
            doc_path = os.path.join(folder_path, filename)
            doc_to_pdf(doc_path, output_dir=folder_path, soffice_path=soffice_path)

if __name__ == "__main__":
    carpeta_docs = "./doc"  # Cambia por la ruta si no está en la carpeta actual
    convertir_carpeta_docs(carpeta_docs)
