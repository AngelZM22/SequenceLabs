import os
import requests


REPOSITORIO = "https://api.github.com/repos/statsbomb/open-data/contents/data"
CARPETAS = ["matches", "events", "three-sixty"]
LOCALDATASET_PATH = "data"

GITHUB_TOKEN = "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"  # Reemplaza con tu token personal de GitHub si es necesario
TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def descargar_archivos_carpeta_rec(url_api, carpeta_local):
    response = requests.get(url_api, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error al acceder a {url_api}: {response.status_code}")
        return

    elementos = response.json()
    for elemento in elementos:
        if elemento["type"]=="file" and elemento["name"].endswith(".json"):
            ruta_destino= os.path.join(carpeta_local, elemento["name"])
            url_descarga = elemento["download_url"]
            r = requests.get(url_descarga, headers=HEADERS)
            if r.status_code == 200:
                os.makedirs(carpeta_local, exist_ok=True)
                with open(ruta_destino, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"{ruta_destino} descargado.")
            else:
                print(f"Error al descargar{ruta_destino}:{r.status_code}")
        elif elemento["type"] == "dir":
            nueva_api = elemento["url"]
            nueva_carpeta = os.path.join(carpeta_local, elemento["name"])
            descargar_archivos_carpeta_rec(nueva_api, nueva_carpeta)

def descargar_competitions():
    os.makedirs(LOCALDATASET_PATH, exist_ok=True)

    # Descargar competitions.json directamente
    url_competitions = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"
    r = requests.get(url_competitions, headers=HEADERS)
    if r.status_code == 200:
        with open(f"{LOCALDATASET_PATH}/competitions.json", "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Competitions.json descargado correctamente.")
    else:
        print("Error al descargar Competitions.json")

def descargar_datos():
    descargar_competitions()

    for carpeta in CARPETAS:
        carpeta_local=os.path.join(LOCALDATASET_PATH,carpeta)
        url = f"{REPOSITORIO}/{carpeta}"
        descargar_archivos_carpeta_rec(url,carpeta_local)

if __name__== "__main__":
    descargar_datos()