import asyncio
from playwright.async_api import async_playwright
import time
import random
import os

PROMO_URL = "https://seller.indotrading.com/default/listproduct"
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL", "cahayasaktipratama@yahoo.co.id")
LOGIN_PASS = os.getenv("LOGIN_PASS", "cahaya123")
SESSION_DIR = ".auth"
WAIT_MINUTES = 64

async def ensure_login(page):
    await page.goto(PROMO_URL)
    if "login" not in page.url.lower():
        print("✅ Sudah login.")
        return

    print("🔐 Login diperlukan...")
    iframe = page.frame_locator("iframe[src*='indotrading.com/newloginv2']")
    await iframe.locator("input[name='email']").fill(LOGIN_EMAIL)
    await iframe.locator("button:has-text('Selanjutnya')").click()
    await iframe.locator("input[type='password']").fill(LOGIN_PASS)
    await iframe.locator("button:has-text('LOGIN')").click()
    await page.wait_for_timeout(5000)
    print("✅ Login berhasil.")

async def promote(page):
    await page.goto(PROMO_URL)
    print("🌐 Membuka halaman promo...")

    try:
        await page.locator("i.fa-angle-double-right").click(timeout=5000)
        print("⏩ Klik ke halaman terakhir.")
        await page.wait_for_timeout(2000)
    except:
        print("⚠️ Tidak ada tombol ke halaman terakhir.")

    promoted = 0
    while promoted < 3:
        toggles = await page.locator("table input[type='checkbox'][aria-checked='true']").all()
        if not toggles:
            print("❌ Tidak ada produk aktif, berhenti.")
            break

        target = toggles[-1]
        await target.scroll_into_view_if_needed()
        row = target.locator("xpath=ancestor::tr")
        await row.locator("button:has-text('Aksi')").click()
        await page.wait_for_timeout(1000)

        menu = page.locator(".menuable__content__active div.v-list__tile__title:text('Promosi Produk')")
        await menu.click()
        print(f"🚀 Promosi produk ke-{promoted + 1}")

        try:
            await page.locator("button:has-text('OK')").click(timeout=3000)
            print("✅ Popup OK diklik.")
        except:
            print("⚠️ Tidak muncul popup OK.")

        promoted += 1
        await page.wait_for_timeout(2000)

    print(f"📦 Total produk dipromosikan: {promoted}")

async def main():
    while True:
        print("\n=== Mulai sesi promosi baru ===")
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                SESSION_DIR,
                headless=True,
                args=["--no-sandbox"]
            )
            page = await browser.new_page()

            await ensure_login(page)
            await promote(page)
            await browser.close()

        print(f"💤 Tunggu {WAIT_MINUTES} menit sebelum sesi berikutnya...\n")
        for i in range(WAIT_MINUTES * 60, 0, -1):
            print(f"\r⏳ Menunggu: {i//60:02d}:{i%60:02d}", end="")
            time.sleep(1)
        print()

if __name__ == "__main__":
    asyncio.run(main())
