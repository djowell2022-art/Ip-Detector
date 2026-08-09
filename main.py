import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class IpifyClient:
    URL = "https://api.ipify.org?format=json"

    @staticmethod
    def get_ip() -> str:
        resp = requests.get(IpifyClient.URL, timeout=10)
        resp.raise_for_status()
        return resp.json()["ip"]


class IpinfoClient:
    BASE_URL = "https://ipinfo.io"

    def __init__(self, token: str):
        self.token = token

    def get_geo(self, ip: str) -> dict:
        url = f"{self.BASE_URL}/{ip}/geo"
        params = {"token": self.token}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
        # Оставляем только нужные поля, как в твоём примере
        return {
            "ip": raw.get("ip"),
            "city": raw.get("city"),
            "region": raw.get("region"),
            "country": raw.get("country"),
            "loc": raw.get("loc"),
            "timezone": raw.get("timezone"),
            "org": raw.get("org"),
        }


class YandexDiskClient:
    BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json",
        }

    def create_folder(self, path: str) -> bool:
        url = f"{self.BASE_URL}/resources"
        resp = requests.put(url, headers=self.headers, params={"path": path}, timeout=10)
        if resp.status_code in (201, 409):  # 201 — создана, 409 — уже есть
            return True
        resp.raise_for_status()
        return False

    def get_upload_link(self, path: str) -> str:
        url = f"{self.BASE_URL}/resources/upload"
        resp = requests.get(url, headers=self.headers, params={"path": path}, timeout=10)
        resp.raise_for_status()
        return resp.json()["href"]

    def upload_file(self, upload_url: str, file_path: str) -> None:
        with open(file_path, "rb") as f:
            resp = requests.put(upload_url, data=f, timeout=60)
            resp.raise_for_status()


def main():
    # 1. Получаем IP
    ipify = IpifyClient()
    ip = ipify.get_ip()
    print(f"Текущий IP: {ip}")

    # 2. Получаем геоданные
    token_ipinfo = os.getenv("IPINFO_TOKEN")
    if not token_ipinfo:
        raise ValueError("Не найден IPINFO_TOKEN в .env")
    ipinfo = IpinfoClient(token_ipinfo)
    geo = ipinfo.get_geo(ip)
    print("Геоданные:", geo)

    # 3. Сохраняем в JSON
    result = {"ip": ip, "geo": geo}
    filename = "ip_geo_result.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 4. Загружаем на Яндекс Диск
    token_yd = os.getenv("YANDEX_DISK_TOKEN")
    if not token_yd:
        raise ValueError("Не найден YANDEX_DISK_TOKEN в .env")

    yd = YandexDiskClient(token_yd)
    folder = "/ip_geo_results"
    yd.create_folder(folder)

    remote_path = f"{folder}/ip_geo_result.json"
    upload_url = yd.get_upload_link(remote_path)
    yd.upload_file(upload_url, filename)
    print(f"Файл загружен на Яндекс Диск: {remote_path}")

    # Удаляем локальный файл, чтобы не было лишних файлов
    os.remove(filename)
    print("Локальный файл удалён.")


if __name__ == "__main__":
    main()