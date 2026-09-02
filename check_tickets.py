# -*- coding: utf-8 -*-
# Monitor tiket Buzz Youth Fest #5 (via API resmi Artatix).
# Akurasi status Realtime per Kategori Tiket.

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

def check_is_available(t):
    """
    Memeriksa seluruh kemungkinan parameter Sold Out pada API Artatix.
    """
    if not isinstance(t, dict):
        return False

    # 1. Cek penanda sold out eksplisit
    is_sold_out = t.get("is_sold_out") or t.get("isSoldOut") or t.get("is_soldout")
    if is_sold_out in [True, 1, "1", "true", "True"]:
        return False

    # 2. Cek status teks
    status = str(t.get("status", "")).lower()
    if status in ["sold_out", "soldout", "unavailable", "inactive"]:
        return False

    # 3. Cek stok/kuota tersisa
    quota_keys = ["stock", "quota", "remaining_quota", "available_stock", "qty"]
    for key in quota_keys:
        if key in t and t[key] is not None:
            try:
                if int(t[key]) <= 0:
                    return False
            except (ValueError, TypeError):
                pass

    # 4. Cek apakah ada sub-kategori/varian di dalamnya
    categories = t.get("ticket_categories") or t.get("categories") or t.get("variants")
    if isinstance(categories, list) and len(categories) > 0:
        sub_available = any(check_is_available(sub) for sub in categories)
        if not sub_available:
            return False

    return True

def parse_ticket_info(t):
    """Ambil Kategori, Harga, dan Status Realtime."""
    category = (
        t.get("ticket_category_name") 
        or t.get("category_name") 
        or t.get("name") 
        or t.get("title") 
        or "Kategori Tiket"
    )

    raw_price = t.get("price") or t.get("price_formatted") or 0
    price_str = format_rupiah(raw_price)

    is_available = check_is_available(t)

    return {
        "category": str(category).replace("*", "").replace("_", ""),
        "price": price_str,
        "is_available": is_available
    }

def summarize_all(tickets):
    """Format daftar status kategori tiket."""
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

    # Hanya kirim pesan jika ADA setidaknya 1 tiket yang READY / RESTOCK
    if not has_ready_ticket:
        print("Semua kategori tiket saat ini SOLD OUT. Tidak mengirim notifikasi ke Telegram.")
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
