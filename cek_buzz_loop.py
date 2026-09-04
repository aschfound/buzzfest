# -*- coding: utf-8 -*-
# Monitor Stok Realtime Semua Kategori - Buzz Youth Fest #5 (Versi Loop / VPS)
#
# Script ini akan berjalan TERUS-MENERUS (loop) selama proses ini aktif.
# Semakin dekat dengan waktu target penjualan, semakin sering dia mengecek API.
#
# Cara menjalankan di VPS supaya tetap hidup walau SSH terputus:
#   nohup python3 cek_buzz_loop.py > buzz.log 2>&1 &
# atau pakai screen/tmux:
#   screen -S buzz
#   python3 cek_buzz_loop.py
#   (lalu Ctrl+A, D untuk detach)

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ============ KONFIGURASI ============

API_TICKET_URL = "https://api.artatix.co.id/api/v1/customer/ticket/buzz_youth_fest_5?isTicketExclusive=0"
BUY_URL = "https://artatix.co.id/event/buzz_youth_fest_5/ticket"

# Waktu target penjualan dibuka (WIB / UTC+7), sesuai dateStart di API
WIB = timezone(timedelta(hours=7))
TARGET_TIME = datetime(2026, 9, 8, 13, 0, 0, tzinfo=WIB)

# Berapa menit sebelum TARGET_TIME mulai masuk mode "polling cepat"
FAST_POLL_WINDOW_MINUTES = 5

# Interval cek (detik) di masing-masing mode
INTERVAL_JAUH = 120     # jauh dari waktu target -> cek tiap 2 menit (hemat resource)
INTERVAL_DEKAT = 15     # < 30 menit dari target -> cek tiap 15 detik
INTERVAL_CEPAT = 3      # masuk FAST_POLL_WINDOW_MINUTES -> cek tiap 3 detik

# Berhenti otomatis setelah notif pertama berhasil terkirim?
STOP_AFTER_FIRST_NOTIF = True

# Kalau proses berjalan lebih dari ini tanpa hasil, otomatis berhenti (jaga-jaga)
MAX_RUNTIME_HOURS = 6

NOT_AVAILABLE_STATUSES = {"not started", "sold out", "ended", "expired", "closed"}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Origin": "https://artatix.co.id",
    "Referer": BUY_URL,
}

# ============ FUNGSI-FUNGSI ============

def format_rupiah(amount):
    try:
        val = int(float(amount))
        return f"Rp{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(amount)

def fetch_ticket_data():
    req = urllib.request.Request(API_TICKET_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("data") or []

def send_telegram(message):
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

def send_telegram_text(text):
    """Kirim pesan teks biasa (untuk notif start/stop/error), tanpa tombol beli."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(text)
        return
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(payload).encode("utf-8"), method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Gagal kirim pesan status: {e}")

def get_interval(now):
    """Tentukan interval polling berdasarkan seberapa dekat dengan TARGET_TIME."""
    delta = (TARGET_TIME - now).total_seconds()
    if delta <= 0:
        return INTERVAL_CEPAT
    if delta <= FAST_POLL_WINDOW_MINUTES * 60:
        return INTERVAL_CEPAT
    if delta <= 30 * 60:
        return INTERVAL_DEKAT
    return INTERVAL_JAUH

def check_once():
    """Satu kali pengecekan. Return True jika ada tiket ready & notif terkirim."""
    try:
        tickets = fetch_ticket_data()
    except Exception as e:
        print(f"[{datetime.now(WIB).strftime('%H:%M:%S')}] Gagal mengambil data tiket: {e}")
        return False

    if not tickets:
        print(f"[{datetime.now(WIB).strftime('%H:%M:%S')}] Data tiket tidak ditemukan.")
        return False

    results = []
    has_ready_ticket = False

    for t in tickets:
        category = t.get("category") or t.get("name") or "Tiket"
        price = format_rupiah(t.get("price", 0))
        stock = t.get("stock")
        status_raw = str(t.get("status", "")).strip()
        status_text = status_raw.lower()

        is_not_available_status = status_text in NOT_AVAILABLE_STATUSES
        try:
            stock_val = int(stock)
            has_stock = stock_val > 0
        except (TypeError, ValueError):
            has_stock = True

        is_available = (not is_not_available_status) and has_stock

        if is_available:
            status_tag = "🟢 *[READY]*"
            has_ready_ticket = True
        else:
            status_tag = f"🔴 *[{status_raw.upper() or 'UNAVAILABLE'}]*"

        stock_info = f" (stok: {stock})" if stock is not None else ""
        results.append(f"{status_tag} {category} - {price}{stock_info}")

    timestamp = datetime.now(WIB).strftime('%H:%M:%S')
    ringkas = ", ".join(
        f"{t.get('category', '?')}:{t.get('status', '?')}" for t in tickets
    )
    print(f"[{timestamp}] {ringkas}")

    if not has_ready_ticket:
        return False

    summary_text = "\n".join(results)
    message = (
        "⚡ *TIKET TERSEDIA! BUZZ YOUTH FEST #5*\n\n"
        f"{summary_text}\n\n"
        "Segera buka browser di HP dan lakukan checkout manual sebelum kehabisan!"
    )
    print(f"[{timestamp}] Tiket READY terdeteksi! Mengirim notifikasi ke Telegram...")
    send_telegram(message)
    return True

def main():
    start_time = datetime.now(WIB)
    print(f"Memulai monitor Buzz Youth Fest #5 pada {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Target waktu penjualan dibuka: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    send_telegram_text(
        f"🤖 Monitor Buzz Youth Fest #5 dimulai.\nTarget: {TARGET_TIME.strftime('%d %b %Y %H:%M WIB')}"
    )

    max_runtime = timedelta(hours=MAX_RUNTIME_HOURS)

    try:
        while True:
            now = datetime.now(WIB)

            if now - start_time > max_runtime:
                print("Batas waktu maksimum tercapai. Menghentikan monitor.")
                send_telegram_text("⏹️ Monitor Buzz Youth Fest #5 berhenti otomatis (batas waktu maksimum tercapai, belum ada tiket ready).")
                break

            found = check_once()

            if found and STOP_AFTER_FIRST_NOTIF:
                print("Notifikasi terkirim. Menghentikan monitor.")
                break

            interval = get_interval(now)
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nMonitor dihentikan manual (Ctrl+C).")
        send_telegram_text("⏹️ Monitor Buzz Youth Fest #5 dihentikan manual.")
        sys.exit(0)

if __name__ == "__main__":
    main()
