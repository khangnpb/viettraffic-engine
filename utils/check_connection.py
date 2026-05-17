import requests
import urllib3
urllib3.disable_warnings()

url = 'https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id=5d8cd4ee766c880017188946&bg=black&w=520&h=300'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://giaothong.hochiminhcity.gov.vn/'
}

print(f"[*] Checking URL: {url}")
try:
    r = requests.get(url, headers=headers, timeout=15, verify=False)
    print(f"[+] Status Code: {r.status_code}")
    print(f"[+] Content Type: {r.headers.get('Content-Type')}")
    print(f"[+] Content Length: {len(r.content)} bytes")
    if len(r.content) > 100:
        print("[+] Connection OK, received image data.")
    else:
        print("[-] Connection success but no data (empty image).")
except Exception as e:
    print(f"[!] Connection Error: {e}")
