# -*- coding: utf-8 -*-
# Script Full Auto-Checkout Artatix - Pop Styles Fun Run

import json
import os
import sys
import urllib.parse
import urllib.request

# 1. ENDPOINT API RESMI ARTATIX
CHECKSTOCK_URL = "https://api.artatix.co.id/api/v1/customer/ticket/checkstock"
TRANSACTION_URL = "https://api.artatix.co.id/api/v1/customer/transaction"
BUY_URL = "https://artatix.co.id/event/pop_styles_fun_run/ticket"

# 2. DATA SESI & TOKEN (Tempelkan hasil copy dari Network Tab F12)
USER_COOKIE = "_ga=GA1.1.1190656932.1788362821; _ga_MPWXGDPRG4=GS2.1.s1788362821$o1$g1$t1788363832$j60$l0$h0; UPSTREAMID=e7f3c70e94117f134a7804068cb52eab; SRVGROUP=common; cf_clearance=BorCmC5gHBfaiV3uZeD__gfND8YTSV_TRH8OxYECah8-1788364026-1.2.1.1-xx7cXVaiUqUymlGvjcdkww82UTHzsWzrziJiYDFAb26IdW0OGvxIvSzP98MlK.oRsPXsZo1MhSZeYDNWP2UJJUx_N5xMCINETk11IZ0eq.dA779ZVsxkFhxgafi2idX5_axyW4Ckqc4sA.chsV90JDBJHIYGfbp1WUWbbVEdldJl_bExCKKlzcPN_WD.HGpBG_aOOozAH.c50ph9Uiiwa8M903K8nhTpd0DFlkcVdrehXEgfsM_RVTRvPkPspMt3kaYTOIjxJ720BQ8N7YNeulgt0ad_zmuc4iM66NKaewzGeR_BZ.qSSvwNIUhBKMQS01.11mOct4tbPbXFtU.rXeTrXZ3qCA5GQw6Ucq3dSnllS_8TnMDd9thtO34.4OR6K9uYbi6MmlxJlcK0U9cL87yDe1ZRqBCZQnAot6f1Dg_IpIVOKo1xvwWhhyp7Zfkav43nfNbr4Dh8Vkavbh8YPEpfgrWWKSOYqdI6uth1k8I"
CF_TOKEN = "1.YTreVSULb2juBSxRd0f-uUqENOQdyJ17Pp-A-3GebAqNn948BE-e6zt2-Gq2ynNxYaZnPLyYubECczVffg4u0bRhl8HdirgvWPLouLGNYXyoNwcZAbuATHDyQPaJKgzYU1sBtTb6YJny9XXqavZ6x5dCw76GqViP8rjfW2mefsqKSghwC1pVBGGoTL5jjW2n3AUUwuPISL6bYIrSYaukLfIblmTqgMdSmrGKkmSSrou1mcJzqbY3E8aVBG2X5eVWoDmp5YVcoVQKpfyXi5as3vJdXEdxtHOufbqXw42XftEYATTlk4WOSJlEzF9_qAUO36lQNcyKy7I23nWj-et9_lJ-p1XQxBTQn9hqST51LULPDpRodKbIGgO8cVH5woXixLoM6AKi2Tp7b9HyfiHhExLwUasuS2f0VV57N10Z66EGkM1gMxgyTHcHd2wnAU2oQ8nF1HWJ39UfMh1vqeCnvPpQ9MwjjoxlPuOu6EpWKc46SEerfgsMb-rF4Y_Mh-xnWBZHRBvITTMl5vrYO77FtM5V_YeZZQXqwPXKdg7M3UlOFW7QuOaFfNrOFHFFfg_96EKgPGWrqR_DMJOIoZErC8dOK22jCvB45Vga--6AmyQIqMNYkrj3RXNgaB2Wr0-g_wpl8-O_2bIJkNMD23mUOzoQuHoaP_mxNOAu41KJSHfEzpw--RipvDa_u9eCm9RoGdqU136rmMBZTpjzfoRTRw.J6vOhuZMBB2EJ8mAc75Xrg.d5b59a03126a301c9648c79cc8d04afce5b5630415f7be47f8d04339889e5855"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Cookie": USER_COOKIE,
    "Origin": "https://artatix.co.id",
    "Referer": BUY_URL,
}

# 3. PARAMETER EVENT POP STYLES FUN RUN
EVENT_ID = 2564
TARGET_TICKET_ID = 19451  # ID Tiket Pop Styles Fun Run yang kamu pilih

PAYLOAD_ORDER = {
    "cfToken": CF_TOKEN,
    "eventId": EVENT_ID,
    "lat": "-2.898100150733048",
    "lng": "104.68216920861332",
    "paymentMethod": "qris",
    "orderDetail": {
        "fullname": "Dimas Baskara",
        "identityType": "KTP",
        "identityNumber": "1674020803980002",
        "email": "hichitzy@gmail.com",
        "phone": "081234567890"  # Sesuaikan dengan nomor HP aktifmu
    },
    "tickets": [
        {
            "id": TARGET_TICKET_ID,
            "qty": 1,
            "seats": []
        }
    ]
}

def check_stock(ticket_id):
    """Cek stok realtime via endpoint checkstock."""
    payload = {"tickets": [{"id": ticket_id, "qty": 1}]}
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(CHECKSTOCK_URL, data=data_bytes, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Gagal cek stok: {e}")
        return None

def execute_transaction():
    """Tembak API transaksi akhir untuk membuat pesanan & QRIS."""
    data_bytes = json.dumps(PAYLOAD_ORDER).encode("utf-8")
    req = urllib.request.Request(TRANSACTION_URL, data=data_bytes, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Transaksi Gagal: {e}")
        return None

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode()
    
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode() == 200
    except:
        return False

def main():
    print(f"Mengecek stok Pop Styles Fun Run (ID Tiket: {TARGET_TICKET_ID})...")
    stock_res = check_stock(TARGET_TICKET_ID)
    print("Respon Stok:", stock_res)

    print("\nEksekusi pemesanan otomatis ke Artatix...")
    trx_res = execute_transaction()
    
    if trx_res and (trx_res.get("success") or trx_res.get("status") in [200, 201]):
        print("\nBERHASIL CHECKOUT!")
        print(json.dumps(trx_res, indent=2))
        
        payment_data = trx_res.get("data", {})
        qr_url = payment_data.get("qrUrl") or payment_data.get("paymentUrl") or BUY_URL
        
        msg = (
            f"⚡ *BERHASIL CHECKOUT POP STYLES FUN RUN!*\n\n"
            f"Kategori Tiket: ID {TARGET_TICKET_ID}\n"
            f"Segera bayar di link berikut:\n{qr_url}"
        )
        send_telegram(msg)
    else:
        print("\nCheckout gagal atau sesi habis. Respon Server:")
        print(json.dumps(trx_res, indent=2) if trx_res else "No Response")

if __name__ == "__main__":
    main()