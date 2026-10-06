import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_URL = "https://buildbot.libretro.com/nightly/android/"

def extract_and_download_apks(page_url, target_folder="downloaded_apks"):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    print(f"Connecting to website: {page_url}...")
    try:
        response = requests.get(page_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing website: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    dated_files = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.apk'):
            # Pega apenas o nome do arquivo final, descartando caminhos relativos
            clean_name = href.split('/')[-1]
            
            # Verifica se o arquivo começa com um padrão de data válido (ex: 2026-)
            if len(clean_name) >= 10 and clean_name[:4].isdigit() and clean_name[4] == '-':
                dated_files.append(clean_name)

    if not dated_files:
        print("Nenhum arquivo APK datado foi encontrado na página.")
        return

    # Ordena alfabeticamente para colocar as datas mais recentes no final
    dated_files.sort()
    latest_file = dated_files[-1]
    
    # Extrai os 10 primeiros caracteres (Ex: 2026-10-06)
    latest_date_str = latest_file[:10]
    print(f"Data mais recente identificada no servidor: {latest_date_str}")

    # Define os três alvos exatos com data requisitados
    targets = {
        "universal": f"{latest_date_str}-RetroArch.apk",
        "arm64": f"{latest_date_str}-RetroArch_aarch64.apk",
        "arm32": f"{latest_date_str}-RetroArch_ra32.apk"
    }

    downloaded_any = False
    for arch, file_name in targets.items():
        # Une a URL base do site diretamente com o nome limpo do arquivo datado
        download_url = urljoin(page_url, file_name)
        save_path = os.path.join(target_folder, file_name)
        
        try:
            print(f"Baixando ({arch}): {file_name}")
            with requests.get(download_url, stream=True) as r:
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Download concluído: {file_name}")
                    downloaded_any = True
                else:
                    print(f"⚠️ Arquivo não disponível no servidor (Status {r.status_code}): {file_name}")
        except Exception as e:
            print(f"❌ Erro ao processar {file_name}: {e}")

    # Envia a tag correta para o GitHub Actions criar o card de Release
    if downloaded_any:
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as out_file:
                out_file.write(f"tag={latest_date_str}\n")
            print(f"Tag {latest_date_str} exportada com sucesso.")

if __name__ == "__main__":
    extract_and_download_apks(TARGET_URL)
