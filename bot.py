"""
$BERT Portfolio Flex Bot for Telegram.

Commands:
  /flex <wallet_address>  - Generate your $BERT flex card
  /flex                   - Show help message
  /start                  - Welcome message
  /price                  - Quick price check

Usage:
  1. Set TELEGRAM_BOT_TOKEN in .env
  2. (Optional) Set SOLANA_RPC_URL for a premium RPC
  3. python bot.py
"""

import asyncio
import logging
import re

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, TOKEN_TICKER, TOKEN_NAME, TOKEN_MINT
from solana_client import get_wallet_data, get_token_price
from card_generator import generate_flex_card

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Simple rate limiting (wallet -> last request timestamp)
_rate_limit: dict[str, float] = {}
RATE_LIMIT_SECONDS = 15  # one flex per wallet per 15s

# Solana address regex (base58, 32-44 chars)
SOLANA_ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome = (
        f"🐶 <b>Welcome to the {TOKEN_TICKER} Flex Bot!</b>\n\n"
        f"Show off your <b>{TOKEN_NAME}</b> bag with a custom cyberpunk flex card.\n\n"
        f"<b>Commands:</b>\n"
        f"  /flex &lt;wallet&gt; — Generate your flex card\n"
        f"  /price — Quick price check\n\n"
        f"<i>Paste your Solana wallet address to flex on the timeline.</i> 💎"
    )
    await update.message.reply_text(welcome, parse_mode="HTML")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command."""
    await update.message.reply_text(f"⏳ Fetching {TOKEN_TICKER} price...")

    price_data = await get_token_price()
    if not price_data:
        await update.message.reply_text("❌ Couldn't fetch price data. Try again later.")
        return

    change = price_data["price_change_24h"]
    arrow = "🟢 ▲" if change >= 0 else "🔴 ▼"

    mcap = price_data["market_cap"]
    mcap_str = f"${mcap / 1_000_000:.2f}M" if mcap >= 1_000_000 else f"${mcap:,.0f}"

    vol = price_data["volume_24h"]
    vol_str = f"${vol / 1_000_000:.2f}M" if vol >= 1_000_000 else f"${vol:,.0f}"

    msg = (
        f"<b>{TOKEN_TICKER} Price Update</b>\n\n"
        f"💰 Price: <code>${price_data['price_usd']:.8f}</code>\n"
        f"{arrow} 24h: <b>{change:+.2f}%</b>\n"
        f"📊 MCap: <b>{mcap_str}</b>\n"
        f"📈 24h Vol: <b>{vol_str}</b>\n\n"
        f"<i>/flex &lt;wallet&gt; to show off your bag!</i>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def flex_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /flex <wallet_address> command."""
    import time

    # Parse wallet address from args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            f"🐶 <b>How to flex:</b>\n\n"
            f"<code>/flex YourSolanaWalletAddress</code>\n\n"
            f"Paste your Solana wallet address after /flex to generate your {TOKEN_TICKER} flex card!",
            parse_mode="HTML",
        )
        return

    wallet = context.args[0].strip()

    # Validate address format
    if not SOLANA_ADDR_RE.match(wallet):
        await update.message.reply_text(
            "❌ That doesn't look like a valid Solana wallet address.\n"
            "It should be 32-44 characters of base58 (letters and numbers, no 0/O/I/l)."
        )
        return

    # Rate limit check
    now = time.time()
    if wallet in _rate_limit and now - _rate_limit[wallet] < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - (now - _rate_limit[wallet]))
        await update.message.reply_text(f"⏳ Cooldown! Try again in {remaining}s.")
        return
    _rate_limit[wallet] = now

    # Send "generating" message
    status_msg = await update.message.reply_text(
        f"⚡ Generating {TOKEN_TICKER} flex card...\n"
        f"<i>Scanning wallet on Solana...</i>",
        parse_mode="HTML",
    )

    try:
        # Fetch all wallet data
        data = await get_wallet_data(wallet)

        # Check if they actually hold any tokens
        if data["balance"] is None:
            await status_msg.edit_text(
                "❌ Couldn't read wallet data. Check the address and try again."
            )
            return

        if data["balance"] == 0:
            await status_msg.edit_text(
                f"😢 This wallet doesn't hold any {TOKEN_TICKER}!\n\n"
                f"Buy some $BERT first, then come back to flex. 🐶"
            )
            return

        # Generate the card
        card_image = generate_flex_card(data)

        # Build caption
        caption = (
            f"🐶 <b>{TOKEN_TICKER} FLEX</b> by {data['wallet_short']}\n\n"
            f"💰 {data['balance_formatted']} BERT (≈ {data['usd_value_formatted']})\n"
            f"💎 Holding for: {data['hold_duration']}\n\n"
            f"<i>Flex your bag → /flex</i>"
        )

        # Delete the "generating" message
        await status_msg.delete()

        # Send the flex card
        await update.message.reply_photo(
            photo=InputFile(card_image, filename="bert_flex_card.png"),
            caption=caption,
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Flex card error: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Something went wrong generating your flex card.\n"
            "The Solana RPC might be rate-limited. Try again in a minute!"
        )


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error: {context.error}")


def main():
    """Start the bot."""
    import asyncio

    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: Set TELEGRAM_BOT_TOKEN in .env file!")
        print("   1. Talk to @BotFather on Telegram")
        print("   2. Create a new bot")
        print("   3. Copy the token to .env")
        return

    print(f"🐶 Starting {TOKEN_TICKER} Flex Bot...")
    print(f"   Token: {TOKEN_NAME}")
    print(f"   Mint:  {TOKEN_MINT}")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("flex", flex_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_error_handler(handle_error)

    # Run with explicit event loop (fixes Python 3.14)
    print("✅ Bot is running! Send /flex <wallet> in your Telegram group.")

    async def run():
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            # Keep running forever
            while True:
                await asyncio.sleep(3600)

    asyncio.run(run())


if __name__ == "__main__":
    main()
