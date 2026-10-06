import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Endereço oficial do servidor da Libretro
TARGET_URL = "https://libretro.com"

def extract_and_download_apks(page_url, target_folder="downloaded_apks"):
    # Cria a pasta temporária para salvar os arquivos antes de mandar para a Release
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    print(f"Conectando ao site: {page_url}...")
    try:
        response = requests.get(page_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o site: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    dated_files = []
    
    # Captura todos os links de APK que comecem com "202" (padrão de ano atual)
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.apk'):
            if href.startswith("202"):
                dated_files.append(href)

    if not dated_files:
        print("Nenhum arquivo APK datado foi encontrado na página.")
        return

    # Ordena a lista alfabeticamente. Isso joga a data mais nova automaticamente para o fim da lista
    dated_files.sort()
    latest_file = dated_files[-1]
    
    # Isola os primeiros 10 caracteres do nome (Ex: "2026-10-06")
    latest_date_str = latest_file[:10]
    print(f"Data mais recente detectada no servidor: {latest_date_str}")

    # Define os três alvos exatos com o padrão de data idêntico ao da imagem
    targets = {
        "universal": f"{latest_date_str}-RetroArch.apk",
        "arm64": f"{latest_date_str}-RetroArch_aarch64.apk",
        "arm32": f"{latest_date_str}-RetroArch_ra32.apk"
    }

    downloaded_any = False
    for arch, file_name in targets.items():
        download_url = urljoin(page_url, file_name)
        save_path = os.path.join(target_folder, file_name)
        
        try:
            print(f"Baixando ({arch}): {file_name} de {download_url}")
            with requests.get(download_url, stream=True) as r:
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Download concluído com sucesso: {file_name}")
                    downloaded_any = True
                else:
                    print(f"⚠️ Arquivo não encontrado no servidor (Status {r.status_code}): {file_name}")
        except Exception as e:
            print(f"❌ Erro ao baixar o arquivo {file_name}: {e}")

    # Avisa o GitHub Actions qual Tag de data foi usada para batizar a Release pública
    if downloaded_any:
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as out_file:
                out_file.write(f"tag={latest_date_str}\n")
            print(f"Tag enviada com sucesso para o GitHub Actions: {latest_date_str}")

if __name__ == "__main__":
    extract_and_download_apks(TARGET_URL)
