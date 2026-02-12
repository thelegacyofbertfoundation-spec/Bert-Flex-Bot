"""
Solana on-chain data fetcher for $BERT token.
Fetches token balance, price, holder rank, and first buy date.
"""

import httpx
import base64
import struct
from datetime import datetime, timezone
from config import (
    SOLANA_RPC_URL, TOKEN_MINT, TOKEN_DECIMALS, DEXSCREENER_URL
)

# SPL Token Program ID
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


async def _rpc_call(method: str, params: list) -> dict:
    """Make a JSON-RPC call to Solana."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            SOLANA_RPC_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )
        return resp.json()


async def get_token_balance(wallet_address: str) -> float | None:
    """Get the $BERT token balance for a wallet."""
    try:
        result = await _rpc_call(
            "getTokenAccountsByOwner",
            [
                wallet_address,
                {"mint": TOKEN_MINT},
                {"encoding": "jsonParsed"},
            ],
        )
        accounts = result.get("result", {}).get("value", [])
        if not accounts:
            return 0.0

        total = 0.0
        for acc in accounts:
            info = acc["account"]["data"]["parsed"]["info"]["tokenAmount"]
            total += float(info["uiAmount"] or 0)
        return total
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return None


async def get_token_price() -> dict | None:
    """Get current $BERT price and market data from DexScreener."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(DEXSCREENER_URL)
            data = resp.json()

        pairs = data.get("pairs", [])
        if not pairs:
            return None

        # Pick the pair with highest liquidity
        pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0)))
        return {
            "price_usd": float(pair.get("priceUsd", 0)),
            "market_cap": float(pair.get("marketCap", 0) or pair.get("fdv", 0)),
            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
        }
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None


async def get_first_buy_timestamp(wallet_address: str) -> datetime | None:
    """
    Approximate the first time this wallet received $BERT tokens.
    Uses getSignaturesForAddress on the token account.
    """
    try:
        # First, find the token account address
        result = await _rpc_call(
            "getTokenAccountsByOwner",
            [
                wallet_address,
                {"mint": TOKEN_MINT},
                {"encoding": "jsonParsed"},
            ],
        )
        accounts = result.get("result", {}).get("value", [])
        if not accounts:
            return None

        token_account = accounts[0]["pubkey"]

        # Get the oldest signatures for this token account
        sigs_result = await _rpc_call(
            "getSignaturesForAddress",
            [
                token_account,
                {"limit": 1000},  # Get as many as we can
            ],
        )
        signatures = sigs_result.get("result", [])
        if not signatures:
            return None

        # The last signature in the list is the oldest
        oldest = signatures[-1]
        block_time = oldest.get("blockTime")
        if block_time:
            return datetime.fromtimestamp(block_time, tz=timezone.utc)
        return None
    except Exception as e:
        print(f"Error fetching first buy: {e}")
        return None


async def get_holder_rank(wallet_address: str) -> dict | None:
    """
    Get approximate holder rank using DexScreener or Birdeye data.
    Falls back to a simulated rank based on balance percentile.
    """
    try:
        # Use Helius DAS API or fallback
        # For now, we'll use a simple approach: fetch top holders
        # via the getTokenLargestAccounts RPC method
        result = await _rpc_call("getTokenLargestAccounts", [TOKEN_MINT])
        largest = result.get("result", {}).get("value", [])

        if not largest:
            return None

        # Check if our wallet's token account is in top 20
        accounts_result = await _rpc_call(
            "getTokenAccountsByOwner",
            [
                wallet_address,
                {"mint": TOKEN_MINT},
                {"encoding": "jsonParsed"},
            ],
        )
        user_accounts = accounts_result.get("result", {}).get("value", [])
        if not user_accounts:
            return {"rank": None, "total_holders": len(largest), "top_20": False}

        user_pubkey = user_accounts[0]["pubkey"]
        user_balance = float(
            user_accounts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] or 0
        )

        # Check rank among largest holders
        for i, holder in enumerate(largest):
            if holder["address"] == user_pubkey:
                return {
                    "rank": i + 1,
                    "total_holders": "20+",
                    "top_20": True,
                }

        # Not in top 20 — estimate rank based on balance comparison
        if largest:
            smallest_top = float(largest[-1]["uiAmount"] or 0)
            if user_balance > 0 and smallest_top > 0:
                ratio = user_balance / smallest_top
                if ratio > 0.5:
                    est_rank = 20 + int((1 - ratio) * 30)
                elif ratio > 0.1:
                    est_rank = 50 + int((1 - ratio) * 200)
                else:
                    est_rank = 250 + int((1 - ratio) * 1000)
                return {
                    "rank": est_rank,
                    "total_holders": "est.",
                    "top_20": False,
                }

        return {"rank": None, "total_holders": "unknown", "top_20": False}

    except Exception as e:
        print(f"Error fetching holder rank: {e}")
        return None


async def get_wallet_data(wallet_address: str) -> dict:
    """Fetch all data needed for the flex card."""
    import asyncio

    balance, price_data, first_buy, rank_data = await asyncio.gather(
        get_token_balance(wallet_address),
        get_token_price(),
        get_first_buy_timestamp(wallet_address),
        get_holder_rank(wallet_address),
    )

    usd_value = None
    if balance is not None and price_data:
        usd_value = balance * price_data["price_usd"]

    # Calculate diamond hands duration
    hold_duration = None
    if first_buy:
        delta = datetime.now(timezone.utc) - first_buy
        days = delta.days
        if days >= 365:
            hold_duration = f"{days // 365}y {(days % 365) // 30}m"
        elif days >= 30:
            hold_duration = f"{days // 30}m {days % 30}d"
        else:
            hold_duration = f"{days}d {delta.seconds // 3600}h"

    return {
        "wallet": wallet_address,
        "wallet_short": f"{wallet_address[:4]}...{wallet_address[-4:]}",
        "balance": balance,
        "balance_formatted": _format_number(balance) if balance else "0",
        "price_usd": price_data["price_usd"] if price_data else None,
        "usd_value": usd_value,
        "usd_value_formatted": _format_usd(usd_value) if usd_value else "$0",
        "market_cap": price_data.get("market_cap") if price_data else None,
        "price_change_24h": price_data.get("price_change_24h") if price_data else None,
        "first_buy": first_buy,
        "hold_duration": hold_duration or "New holder",
        "rank": rank_data.get("rank") if rank_data else None,
        "rank_display": _format_rank(rank_data) if rank_data else "Unranked",
        "top_20": rank_data.get("top_20", False) if rank_data else False,
    }


def _format_number(n: float) -> str:
    """Format large numbers with K/M/B suffixes."""
    if n is None:
        return "0"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.2f}K"
    return f"{n:,.2f}"


def _format_usd(n: float) -> str:
    """Format USD value."""
    if n is None:
        return "$0"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"${n / 1_000:.2f}K"
    if n >= 1:
        return f"${n:,.2f}"
    return f"${n:.4f}"


def _format_rank(rank_data: dict) -> str:
    """Format holder rank display."""
    if not rank_data or rank_data.get("rank") is None:
        return "Unranked"
    rank = rank_data["rank"]
    if rank <= 10:
        return f"🐋 #{rank} (Top 10)"
    if rank <= 50:
        return f"🦈 #{rank} (Top 50)"
    if rank <= 100:
        return f"🐬 #{rank} (Top 100)"
    return f"🐟 ~#{rank}"
