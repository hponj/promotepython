import asyncio
from playwright.async_api import async_playwright
import time, os, datetime

PROMO_URL = "https://seller.indotrading.com/default/listproduct"
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASS = os.getenv("LOGIN_PASS")
SESSION_DIR = ".auth"
WAIT_MINUTES = 64


async def ensure_login(page, log):
    await page.goto(PROMO_URL)
    html = await page.content()  # ✅ gunakan await
    print(html[:500])  # hanya tampilkan sebagian isi HTML agar tidak terlalu panjang

    # cek apakah sudah login
    if "login" not in page.url.lower():
        log.append("✅ Sudah login.")
        return

    log.append("🔐 Login diperlukan...")

    # cek apakah iframe login ada
    iframe = None
    try:
        iframe = page.frame_locator("iframe[src*='indotrading.com/newloginv2']")
        await iframe.locator("input[name='email']").wait_for(timeout=10000)
    except Exception as e:
        log.append(f"⚠️ Gagal menemukan iframe login: {e}")
        await page.screenshot(path="debug_login_iframe_error.png", full_page=True)
        return

    await iframe.locator("input[name='email']").fill(LOGIN_EMAIL)
    await iframe.locator("button:has-text('Selanjutnya')").click()
    await iframe.locator("input[type='password']").fill(LOGIN_PASS)
    await iframe.locator("button:has-text('LOGIN')").click()
    await page.wait_for_timeout(5000)
    log.append("✅ Login berhasil.")


async def promote(page, log):
    # buka halaman promo dan tunggu render
    log.append("🌐 Membuka halaman promo...")
    await page.goto(PROMO_URL)

    try:
        await page.wait_for_load_state("networkidle", timeout=45000)
    except Exception as e:
        log.append(f"⚠️ Timeout load halaman: {e}")
        await page.screenshot(path="debug_timeout.png", full_page=True)
        return

    await page.wait_for_timeout(8000)
    await page.screenshot(path="debug_page.png", full_page=True)
    print("📸 Screenshot debug_page.png sudah diambil.")

    try:
        await page.locator("i.fa-angle-double-right").click(timeout=5000)
        log.append("⏩ Klik ke halaman terakhir.")
        await page.wait_for_timeout(2000)
    except:
        log.append("⚠️ Tidak ada tombol ke halaman terakhir.")

    toggles = await page.locator("table input[type='checkbox']").all()
    log.append(f"📋 Ditemukan {len(toggles)} produk di halaman.")

    promoted = 0
    while promoted < 3:
        if not toggles:
            log.append("❌ Tidak ada produk aktif, berhenti.")
            break

        target = toggles[-1]
        await target.scroll_into_view_if_needed()
        row = target.locator("xpath=ancestor::tr")
        await row.locator("button:has-text('Aksi')").click()
        await page.wait_for_timeout(1000)

        menu = page.locator(
            ".menuable__content__active div.v-list__tile__title:text('Promosi Produk')"
        )
        await menu.click()
        log.append(f"🚀 Promosi produk ke-{promoted + 1}")

        try:
            await page.locator("button:has-text('OK')").click(timeout=3000)
            log.append("✅ Popup OK diklik.")
        except:
            log.append("⚠️ Tidak muncul popup OK.")

        promoted += 1
        await page.wait_for_timeout(2000)

    log.append(f"📦 Total produk dipromosikan: {promoted}")


async def main():
    log = []
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.append(f"\n=== Mulai sesi: {start_time} ===")

    async with async_playwright() as p:
        for attempt in range(2):  # ✅ maksimal 2 kali percobaan
            try:
                browser = await p.chromium.launch_persistent_context(
                    SESSION_DIR,
                    headless=True,  # ubah ke False kalau mau lihat UI
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--window-size=1280,720",
                    ],
                )

                page = await browser.new_page()
                await ensure_login(page, log)
                await promote(page, log)
                await browser.close()
                break  # keluar kalau sukses
            except Exception as e:
                log.append(f"💥 Error pada percobaan {attempt + 1}: {e}")
                await asyncio.sleep(5)
                continue

    with open("playwright_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("\n".join(log))


if __name__ == "__main__":
    asyncio.run(main())
