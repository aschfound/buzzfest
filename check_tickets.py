# -*- coding: utf-8 -*-
# Monitor tiket Buzz Youth Fest #5 (via API resmi Artatix).
# Cek ketersediaan tiket; jika tersedia, kirim notifikasi Telegram + Tombol Direct Link.

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

def summarize(tickets):
    """Ambil nama kategori & harga dari struktur data API (tanpa Markdown berbahaya)."""
    lines = []
    for t in tickets[:8]:
        if isinstance(t, dict):
            name = t.get("name") or t.get("title") or t.get("category") or "Tiket"
            price = t.get("price") or t.get("price_formatted") or ""
            # Menghapus karakter khusus yang bisa merusak parse_mode Telegram
            name = str(name).replace("*", "").replace("_", "")
            if price:
                lines.append(f"• {name}: {price}")
            else:
                lines.append(f"• {name}")
        else:
            lines.append("• Tiket tersedia")
    return "\n".join(lines) if lines else "• Tiket tersedia!"

def send_telegram_with_buttons(message, tickets):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("PERINGATAN: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diatur.")
        print(message)
        return False

    # Buat tombol sederhana ke halaman pembelian utama
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
            status = resp.getcode()
            text = resp.read().decode("utf-8", "replace")[:200]
            print(f"Telegram HTTP {status}: {text}")
            return status == 200
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
        print("Tiket BELUM tersedia (data masih kosong). Monitor akan cek lagi.")
        sys.exit(0)

    print(f"TIKET TERSEDIA! Jumlah entri: {len(tickets)}")
    message = (
        "⚡ TIKET BUZZ YOUTH FEST #5 SUDAH TERSEDIA!\n\n"
        f"{summarize(tickets)}\n\n"
        "Klik tombol di bawah untuk langsung membuka halaman pembelian:"
    )
    
    send_telegram_with_buttons(message, tickets)
    sys.exit(0)

if __name__ == "__main__":
    main()