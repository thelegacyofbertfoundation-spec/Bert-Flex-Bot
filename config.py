"""
$BERT Flex Bot Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Solana
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# $BERT Token
TOKEN_MINT = "HgBRWfYxEfvPhtqkaeymCQtHCrKE46qQ43pKe8HCpump"
TOKEN_TICKER = "$BERT"
TOKEN_NAME = "Bertram The Pomeranian"
TOKEN_DECIMALS = 6  # pump.fun tokens are 6 decimals

# DexScreener API (free, no key needed)
DEXSCREENER_URL = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_MINT}"

# Styling
BRAND_COLOR_PRIMARY = "#00F0FF"    # Neon cyan
BRAND_COLOR_SECONDARY = "#FF00E5"  # Neon magenta
BRAND_COLOR_ACCENT = "#FFD700"     # Gold for rank
CARD_WIDTH = 800
CARD_HEIGHT = 480
