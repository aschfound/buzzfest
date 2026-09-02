# -*- coding: utf-8 -*-
# Monitor tiket Buzz Youth Fest #5 (via API resmi Artatix).
# Cek ketersediaan tiket & status Sold Out secara realtime.

import json
import os
import sys
import urllib.parse
import urllib.request

API_URL = (
    "https://api.artatix.co.id/api/v1/customer/ticket/"
    "buzz_youth_fest_5?isTicketExclusive=0"
)
BUY_URL = "https://artatix.co.id/event/buzz_youth_fest_5/ticket"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

def get_tickets():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("data") or []

def filter_available_tickets(tickets):
    """
    Menyaring tiket yang BENAR-BENAR bisa dibeli.
    Mengecek variabel stok/status yang biasa dipakai API Artatix.
    """
    available = []
    for t in tickets:
        if isinstance(t, dict):
            # Cek berbagai atribut ketersediaan yang umum di API Artatix
            is_sold_out = t.get("is_sold_out") or t.get("isSoldOut")
            status = str(t.get("status", "")).lower()
            stock = t.get("stock") or t.get("quota") or t.get("available_stock")

            # Jika penanda sold_out bernilai True atau status == sold_out, lewati
            if is_sold_out is True or status == "sold_out" or stock == 0:
                continue

            available.append(t)
    return available

def summarize(tickets):
    """Format daftar tiket yang tersedia."""
    lines = []
    for t in tickets[:8]:
        name = t.get("name") or t.get("title") or "Tiket"
        price = t.get("price") or t.get("price_formatted") or ""
        name = str(name).replace("*", "").replace("_", "")
        if price:
            lines.append(f"• {name}: {price}")
        else:
            lines.append(f"• {name}")
    return "\n".join(lines) if lines else "• Tiket tersedia!"

def send_telegram_with_buttons(message, tickets):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("PERINGATAN: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diatur.")
        print(message)
        return False

    inline_keyboard = [
        [{"text": "🎟️ Beli Tiket Sekarang", "url": BUY_URL}]
    ]

    payload = {
        "chat_id": chat_id,
        "text": message,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode() == 200
    except Exception as e:
        print(f"Gagal mengirim pesan Telegram: {e}")
        return False

def main():
    print(f"Mengecek {API_URL} ...")
    try:
        all_tickets = get_tickets()
    except Exception as e:
        print(f"Gagal menghubungi API: {e}")
        sys.exit(2)

    if not all_tickets:
        print("Tiket BELUM rilis di API.")
        sys.exit(0)

    # Filter hanya tiket yang masih ada stoknya (tidak Sold Out)
    available_tickets = filter_available_tickets(all_tickets)

    if not available_tickets:
        print("Semua kategori tiket saat ini SOLD OUT. Menunggu restock...")
        sys.exit(0)

    # Jika ada tiket yang mendadak ready/restock:
    print(f"TIKET READY/RESTOCK! Jumlah tersedia: {len(available_tickets)}")
    message = (
        "⚡ TIKET BUZZ YOUTH FEST #5 READY / RESTOCK!\n\n"
        f"{summarize(available_tickets)}\n\n"
        "Segera buka link pembelian sebelum habis lagi!"
    )
    
    send_telegram_with_buttons(message, available_tickets)
    sys.exit(0)

if __name__ == "__main__":
    main()
