# -*- coding: utf-8 -*-
"""
Tes notifikasi Telegram untuk monitor Buzz Youth Fest #5.
Mengirim satu pesan tes ke chat_id Anda. Jalankan via workflow
"Tes Notifikasi Telegram" atau lokal dengan env yang sama.
"""

from check_tickets import send_telegram

if __name__ == "__main__":
    ok = send_telegram(
        "✅ *TES MONITOR TIKET BYF5*\n\n"
        "Jika Anda menerima pesan ini, notifikasi Telegram sudah benar.\n\n"
        "Anda akan menerima pesan seperti ini saat tiket tersedia:\n"
        "https://artatix.co.id/event/buzz_youth_fest_5/ticket"
    )
    raise SystemExit(0 if ok else 1)
