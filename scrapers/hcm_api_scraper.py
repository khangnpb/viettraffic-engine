import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

async def run():
    # Tạo thư mục lưu log nếu chưa có
    log_dir = "debug_api"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    print(f" [+] Đang khởi tạo... Mọi gói tin sẽ được lưu vào thư mục: {log_dir}")

    counter = 0

    async def handle_response(response):
        nonlocal counter
        # Bắt tất cả các loại gói tin trừ ảnh và font
        if response.request.resource_type in ["xhr", "fetch", "script", "other"]:
            try:
                url = response.url
                # Bỏ qua các file tĩnh phổ biến để đỡ rác
                if any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".css", ".woff"]):
                    return

                text = await response.text()
                if not text:
                    return

                counter += 1
                # Tạo tên file an toàn từ URL
                safe_url = re.sub(r'[^a-zA-Z0-9]', '_', url.split('?')[0])[-50:]
                filename = f"{counter:03d}_{safe_url}.txt"
                filepath = os.path.join(log_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n")
                    f.write("-" * 50 + "\n")
                    f.write(text)
                
                print(f" [Captured {counter:03d}] -> {url[:70]}...")
            except:
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", handle_response)
        
        url = "https://giaothong.hochiminhcity.gov.vn/map.aspx"
        await page.goto(url)
        
        print("\n" + "="*50)
        print("CHẾ ĐỘ QUÉT TOÀN BỘ (BRUTE-FORCE):")
        print("1. Hãy thao tác trên web (tích Camera, di chuyển bản đồ...).")
        print("2. Mỗi khi server gửi dữ liệu, terminal sẽ báo [Captured].")
        print("3. Sau khi xong, hãy vào thư mục 'debug_api' để kiểm tra.")
        print("=" * 50 + "\n")
        
        input("Nhấn ENTER để kết thúc quét...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
