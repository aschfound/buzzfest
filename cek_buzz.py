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
        status_text = str(t.get("status", "")).strip().lower()
        
        # Pengecekan ketat status "Sold Out"
        if status_text == "sold out" or t.get("is_sold_out") is True:
            is_available = False
        else:
            is_available = True

        if is_available:
            status_tag = "🟢 *[READY]*"
            has_ready_ticket = True
        else:
            status_tag = "🔴 *[SOLD OUT]*"

        results.append(f"{status_tag} {category} - {price}")
        print(f"[{'READY' if is_available else 'SOLD OUT'}] {category} - {price}")

    # Jika SEMUA tiket SOLD OUT, hentikan tanpa spam Telegram
    if not has_ready_ticket:
        print("\nHasil Cek Realtime: Semua kategori saat ini SOLD OUT.")
        sys.exit(0)

    # Kirim notifikasi jika ADA minimal 1 tiket yang RESTOCK/READY
    summary_text = "\n".join(results)
    message = (
        "⚡ *RESTOCK DETECTED! BUZZ YOUTH FEST #5*\n\n"
        f"{summary_text}\n\n"
        "Segera buka browser di HP dan lakukan checkout manual sebelum kehabisan!"
    )
    
    print("\nTiket READY terdeteksi! Mengirim notifikasi ke Telegram...")
    send_telegram(message)

if __name__ == "__main__":
    main()
