# -*- coding: utf-8 -*-
# Monitor tiket Buzz Youth Fest #5 (via API resmi Artatix).
# Menampilkan detail kategori, harga berformat Rupiah, dan status Sold Out / Ready.

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

def format_rupiah(amount):
    """Format angka menjadi bentuk Rupiah (Rp475.000)."""
    try:
        val = int(float(amount))
        return f"Rp{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(amount)

def parse_ticket_info(t):
    """Ambil detail Kategori, Harga, dan Status Tiket dari objek API."""
    if not isinstance(t, dict):
        return {"category": "Tiket", "price": "", "is_available": True}

    # Ambil Nama Kategori spesifik
    category = (
        t.get("ticket_category_name") 
        or t.get("category_name") 
        or t.get("name") 
        or t.get("title") 
        or "Kategori Tiket"
    )

    # Format Harga
    raw_price = t.get("price") or t.get("price_formatted") or 0
    price_str = format_rupiah(raw_price)

    # Cek Status Ketersediaan
    is_sold_out = t.get("is_sold_out") or t.get("isSoldOut")
    status = str(t.get("status", "")).lower()
    stock = t.get("stock") if t.get("stock") is not None else t.get("quota")

    is_available = True
    if is_sold_out is True or status == "sold_out" or stock == 0:
        is_available = False

    return {
        "category": str(category).replace("*", "").replace("_", ""),
        "price": price_str,
        "is_available": is_available
    }

def summarize_all(tickets):
    """Format daftar seluruh kategori tiket beserta harganya dan indikator statusnya."""
    lines = []
    has_ready = False

    for t in tickets:
        info = parse_ticket_info(t)
        if info["is_available"]:
            status_tag = "🟢 *[READY]*"
            has_ready = True
        else:
            status_tag = "🔴 *[SOLD OUT]*"

        lines.append(f"{status_tag} {info['category']} - {info['price']}")

    return "\n".join(lines), has_ready

def send_telegram(message):
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode() == 200
    except Exception as e:
        print(f"Gagal mengirim pesan Telegram: {e}")
        return False

def main():
    print(f"Mengecek {API_URL} ...")
    try:
        tickets = get_tickets()
    except Exception as e:
        print(f"Gagal menghubungi API: {e}")
        sys.exit(2)

    if not tickets:
        print("Tiket BELUM rilis di API.")
        sys.exit(0)

    summary_text, has_ready_ticket = summarize_all(tickets)

    # Hanya kirim pesan jika setidaknya ada 1 tiket yang statusnya READY / RESTOCK
    if not has_ready_ticket:
        print("Semua kategori tiket saat ini SOLD OUT. Tidak menyepam Telegram.")
        sys.exit(0)

    print("Ditemukan tiket READY! Mengirim notifikasi...")
    message = (
        "⚡ *STATUS TIKET BUZZ YOUTH FEST #5*\n\n"
        f"{summary_text}\n\n"
        "Segera buka link pembelian sebelum habis lagi!"
    )
    
    send_telegram(message)
    sys.exit(0)

if __name__ == "__main__":
    main()
