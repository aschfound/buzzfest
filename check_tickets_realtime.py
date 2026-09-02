# -*- coding: utf-8 -*-
# Monitor Stok Realtime Semua Kategori - Buzz Youth Fest #5 (Artatix)

import json
import os
import sys
import urllib.parse
import urllib.request

# ENDPOINT RESMI ARTATIX
CHECKSTOCK_URL = "https://api.artatix.co.id/api/v1/customer/ticket/checkstock"
BUY_URL = "https://artatix.co.id/event/buzz_youth_fest_5/ticket"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Origin": "https://artatix.co.id",
    "Referer": BUY_URL,
}

# DAFTAR LENGKAP 7 KATEGORI TIKET BUZZ YOUTH FEST #5
TICKETS_TO_CHECK = [
    {"id": 20000, "name": "PRESALE - PREMIUM", "price": "Rp475.000"},
    {"id": 19999, "name": "PRESALE - FESTIVAL", "price": "Rp300.000"},
    {"id": 20001, "name": "PRESALE - CAT 1", "price": "Rp525.000"},
    {"id": 20002, "name": "PRESALE - CAT 2A", "price": "Rp425.000"},
    {"id": 20003, "name": "PRESALE - CAT 2B", "price": "Rp425.000"},
    {"id": 20004, "name": "PRESALE - CAT 3A", "price": "Rp325.000"},
    {"id": 20006, "name": "PRESALE - CAT 3B", "price": "Rp325.000"},
]

def check_single_ticket_stock(ticket_id):
    """Mengecek stok realtime dengan memeriksa detail data respon."""
    payload = {"tickets": [{"id": ticket_id, "qty": 1}]}
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(CHECKSTOCK_URL, data=data_bytes, headers=HEADERS, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            data = res_json.get("data")

            # Jika data bernilai None / False / Empty
            if not data:
                return False

            # Cek berbagai kemungkinan struktur data stok dari Artatix
            if isinstance(data, dict):
                # 1. Cek jika ada penanda boolean eksplisit
                if data.get("success") is False or data.get("is_available") is False or data.get("is_sold_out") is True:
                    return False
                
                # 2. Cek kuota / stok fisik
                stock = data.get("stock") if data.get("stock") is not None else data.get("available_stock")
                if stock is not None and int(stock) <= 0:
                    return False
                
                # 3. Cek teks status
                status = str(data.get("status", "")).lower()
                if status in ["sold_out", "sold out", "unavailable"]:
                    return False

            elif isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                if isinstance(first_item, dict):
                    stock = first_item.get("stock")
                    if stock is not None and int(stock) <= 0:
                        return False
                    if str(first_item.get("status", "")).lower() in ["sold_out", "sold out"]:
                        return False

            return True
    except Exception:
        # Jika HTTP Error (biasanya 400 Bad Request jika stok habis)
        return False

def send_telegram(message):
    """Mengirimkan notifikasi ke Telegram beserta tombol Beli Tiket."""
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
    
    results = []
    has_ready_ticket = False

    for item in TICKETS_TO_CHECK:
        t_id = item["id"]
        t_name = item["name"]
        t_price = item["price"]

        is_available = check_single_ticket_stock(t_id)
        
        if is_available:
            status_tag = "🟢 *[READY]*"
            has_ready_ticket = True
        else:
            status_tag = "🔴 *[SOLD OUT]*"

        results.append(f"{status_tag} {t_name} - {t_price}")
        print(f"[{'READY' if is_available else 'SOLD OUT'}] {t_name} (ID: {t_id})")

    # Jika SEMUA tiket SOLD OUT, hentikan skrip tanpa spam Telegram
    if not has_ready_ticket:
        print("\nHasil Cek Realtime: Semua kategori saat ini SOLD OUT.")
        sys.exit(0)

    # Kirim notifikasi jika ADA minimal 1 tiket yang READY/RESTOCK
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
