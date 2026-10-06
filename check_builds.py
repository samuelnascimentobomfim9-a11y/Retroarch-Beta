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
    
    # Vasculha todos os links da página de forma simplificada
    for link in soup.find_all('a'):
        href = link.get('href')
        # Pega o texto visível caso o link href seja diferente
        text = link.get_text().strip()
        
        # Procura por qualquer um que termine com .apk e tenha a data de 2026 no nome
        if (href and href.endswith('.apk') and "202" in href) or (text.endswith('.apk') and "202" in text):
            file_name = href if href and href.endswith('.apk') else text
            dated_files.append(file_name)

    if not dated_files:
        print("Nenhum arquivo APK datado foi encontrado na página.")
        return

    # Organiza em ordem alfabética para garantir que as datas mais recentes fiquem por último
    dated_files.sort()
    latest_file = dated_files[-1]
    
    # Extrai os primeiros 10 caracteres correspondentes à data (Ex: 2026-10-06)
    latest_date_str = latest_file[:10]
    print(f"Data mais recente identificada: {latest_date_str}")

    # Monta os alvos com data exatamente como exibido na foto
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
            print(f"Baixando ({arch}): {file_name}")
            with requests.get(download_url, stream=True) as r:
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Download concluído: {file_name}")
                    downloaded_any = True
                else:
                    print(f"⚠️ Arquivo não disponível no servidor: {file_name}")
        except Exception as e:
            print(f"❌ Erro ao processar {file_name}: {e}")

    # Envia o sinalizador com a tag correta para o GitHub criar a Release pública
    if downloaded_any:
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as out_file:
                out_file.write(f"tag={latest_date_str}\n")
            print(f"Tag {latest_date_str} exportada para o GitHub Actions.")

if __name__ == "__main__":
    extract_and_download_apks(TARGET_URL)
