import requests
import time
import os
import json
from telegram import Bot
from datetime import datetime, timezone

# =====================
# 🔐 Zmienne środowiskowe
# =====================
import os
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("8401450027:AAFlXLgcgYGxBQNqnkk4N5-7f9lTyt_bYSs")
CHAT_ID = os.environ.get("1725153905")

bot = Bot(token="8401450027:AAFlXLgcgYGxBQNqnkk4N5-7f9lTyt_bYSs")

# =====================
# ⚡ Ustawienia Volume Bot PRO ALL
# =====================
MIN_VOLUME = 250_000         # minimalny 24h wolumen w USD
MIN_LIQUIDITY = 25_000      # minimalna płynność
CHECK_INTERVAL = 180         # co 3 minuty
SEEN_FILE = "seen_volume_all.json"
VOLUME_INCREASE_THRESHOLD = 0.5  # alert jeśli wolumen wzrósł +50% względem poprzedniego sprawdzenia

# jeśli plik istnieje, wczytaj zapisane tokeny i ich poprzedni wolumen
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = json.load(f)  # format: {token_address: previous_volume}
else:
    seen = {}

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

# =====================
# Rug Check
# =====================
def rug_check(token_address):
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return False
        data = r.json()
        score = data.get("score", 0)
        risks = data.get("risks", [])
        mint_auth = data.get("token", {}).get("mintAuthority")
        freeze_auth = data.get("token", {}).get("freezeAuthority")
        if score < 60:
            return False
        if mint_auth is not None or freeze_auth is not None:
            return False
        if len(risks) > 2:
            return False
        return True
    except:
        return False

# =====================
# Funkcja pobrania par Solana
# =====================
def fetch_pairs():
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    r = requests.get(url)
    return r.json()["pairs"]

# =====================
# Sprawdzenie wolumenu i alert
# =====================
def check_volume():
    print("Sprawdzam wolumen dla wszystkich tokenów...")
    pairs = fetch_pairs()
    for pair in pairs:
        try:
            volume = float(pair.get("volume", {}).get("h24") or 0)
            liquidity = float(pair.get("liquidity", {}).get("usd") or 0)
            token_address = pair["baseToken"]["address"]

            if volume >= MIN_VOLUME and liquidity >= MIN_LIQUIDITY and rug_check(token_address):
                # sprawdzamy wzrost wolumenu
                previous_volume = seen.get(token_address, 0)
                increase = (volume - previous_volume) / previous_volume if previous_volume > 0 else 1.0

                if previous_volume == 0 or increase >= VOLUME_INCREASE_THRESHOLD:
                    message = (
                        f"📈 VOLUME ALERT PRO ALL (SOLANA)\n\n"
                        f"{pair['baseToken']['name']} ({pair['baseToken']['symbol']})\n"
                        f"Volume 24h: ${volume:,.0f}\n"
                        f"Liquidity: ${liquidity:,.0f}\n"
                        f"DEX: {pair['url']}\n"
                        f"{'⚡ Szybki wzrost wolumenu!' if increase >= VOLUME_INCREASE_THRESHOLD else ''}"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Alert wysłany: {pair['baseToken']['symbol']}")

                # zapisujemy aktualny wolumen
                seen[token_address] = volume
                save_seen()

        except Exception as e:
            print("Błąd:", e)

# =====================
# Główna pętla
# =====================
while True:
    try:
        check_volume()
    except Exception as e:
        print("Błąd główny:", e)

    time.sleep(CHECK_INTERVAL)



