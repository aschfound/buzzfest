# -*- coding: utf-8 -*-
# Monitor Stok Realtime Semua Kategori - Buzz Youth Fest #5

import json
import os
import sys
import urllib.parse
import urllib.request

# ENDPOINT UTAMA DATA TIKET BUZZ YOUTH FEST #5
API_TICKET_URL = "https://api.artatix.co.id/api/v1/customer/ticket/buzz_youth_fest_5?isTicketExclusive=0"
BUY_URL = "https://artatix.co.id/event/buzz_youth_fest_5/ticket"

# Status yang dianggap BELUM bisa dibeli.
# "not started"  -> penjualan belum dibuka (dateStart belum tercapai)
# "sold out"     -> tiket habis
# "ended"        -> penjualan sudah ditutup
NOT_AVAILABLE_STATUSES = {"not started", "sold out", "ended", "expired", "closed"}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Origin": "https://artatix.co.id",
    "Referer": BUY_URL,
}

def format_rupiah(amount):
    """Format angka menjadi bentuk Rp475.000."""
    try:
        val = int(float(amount))
        return f"Rp{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(amount)

def fetch_ticket_data():
    """Mengambil data katalog tiket terbaru dari API Artatix."""
    req = urllib.request.Request(API_TICKET_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("data") or []

def send_telegram(message):
    """Mengirim notifikasi ke Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("PERINGATAN: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diatur.")
        print(message)
        return False

    inline_keyboard = [[{"text": "🎟️ Beli Tiket Sekarang", "url": BUY_URL}]]
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode() == 200
    except Exception as e:
        print(f"Gagal mengirim notifikasi Telegram: {e}")
        return False

def main():
    print("Mengecek stok realtime seluruh kategori Buzz Youth Fest #5...")

    try:
        tickets = fetch_ticket_data()
    except Exception as e:
        print(f"Gagal mengambil data tiket: {e}")
        sys.exit(1)

    if not tickets:
        print("Data tiket tidak ditemukan.")
        sys.exit(0)

    results = []
    has_ready_ticket = False

    for t in tickets:
        category = t.get("category") or t.get("name") or "Tiket"
        price = format_rupiah(t.get("price", 0))
        stock = t.get("stock")
        status_raw = str(t.get("status", "")).strip()
        status_text = status_raw.lower()

        # Sebuah kategori dianggap READY hanya jika:
        # 1. Statusnya BUKAN salah satu dari status "belum bisa dibeli"
        #    (Not Started / Sold Out / Ended / dst), DAN
        # 2. Stock-nya lebih dari 0 (kalau field stock tersedia & berupa angka)
        is_not_available_status = status_text in NOT_AVAILABLE_STATUSES

        try:
            stock_val = int(stock)
            has_stock = stock_val > 0
        except (TypeError, ValueError):
            # Kalau field stock tidak berupa angka, jangan jadikan alasan gagal
            has_stock = True

        is_available = (not is_not_available_status) and has_stock

        if is_available:
            status_tag = "🟢 *[READY]*"
            has_ready_ticket = True
        else:
            status_tag = f"🔴 *[{status_raw.upper() or 'UNAVAILABLE'}]*"

        stock_info = f" (stok: {stock})" if stock is not None else ""
        results.append(f"{status_tag} {category} - {price}{stock_info}")
        print(f"[{status_raw or 'UNKNOWN'}] {category} - {price}{stock_info}")

    # Jika TIDAK ADA kategori yang ready, hentikan tanpa spam Telegram
    if not has_ready_ticket:
        print("\nHasil Cek Realtime: Belum ada kategori yang bisa dibeli saat ini.")
        sys.exit(0)

    # Kirim notifikasi jika ADA minimal 1 tiket yang READY/RESTOCK
    summary_text = "\n".join(results)
    message = (
        "⚡ *TIKET TERSEDIA! BUZZ YOUTH FEST #5*\n\n"
        f"{summary_text}\n\n"
        "Segera buka browser di HP dan lakukan checkout manual sebelum kehabisan!"
    )

    print("\nTiket READY terdeteksi! Mengirim notifikasi ke Telegram...")
    send_telegram(message)

if __name__ == "__main__":
    main()
