# -*- coding: utf-8 -*-
"""
Monitor tiket Buzz Youth Fest #5 (via API resmi Artatix).
Cek ketersediaan tiket; jika tersedia, kirim notifikasi Telegram.

Cara pakai lokal:
  set TELEGRAM_BOT_TOKEN=123456:ABC-xxxxxxx
  set TELEGRAM_CHAT_ID=123456789
  python check_tickets.py
"""

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
    """Ambil nama kategori & harga dari struktur data API (fleksibel)."""
    lines = []
    for t in tickets[:8]:
        if isinstance(t, dict):
            name = t.get("name") or t.get("title") or t.get("category") or "Tiket"
            price = t.get("price") or t.get("price_formatted") or ""
            if price:
                lines.append(f"- {name}: {price}")
            else:
                lines.append(f"- {name}")
        else:
            lines.append("- Tiket tersedia")
    return "\n".join(lines) if lines else "- Tiket tersedia!"


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("PERINGATAN: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diatur.")
        print("Pesan tidak terkirim. Isi pesan:")
        print(message)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.getcode()
        text = resp.read().decode("utf-8", "replace")[:200]
    print(f"Telegram HTTP {status}: {text}")
    return status == 200


def main():
    print(f"Mengecek {API_URL} ...")
    try:
        tickets = get_tickets()
    except Exception as e:
        print(f"Gagal menghubungi API: {e}")
        sys.exit(2)  # kode 2 = error jaringan, workflow bisa mencoba lagi nanti

    if not tickets:
        print("Tiket BELUM tersedia (data masih kosong). Monitor akan cek lagi.")
        sys.exit(0)  # belum tersedia = kondisi normal, run dianggap sukses

    print(f"TIKET TERSEDIA! Jumlah entri: {len(tickets)}")
    message = (
        "🎫 *TIKET BUZZ YOUTH FEST #5 SUDAH TERSEDIA!*\n\n"
        f"{summarize(tickets)}\n\n"
        f"Beli sekarang (login dulu di HP):\n{BUY_URL}\n\n"
        "Max 5 tiket per transaksi. Buruan sebelum habis!"
    )
    send_telegram(message)
    sys.exit(0)  # kode 0 = tiket tersedia


if __name__ == "__main__":
    main()
