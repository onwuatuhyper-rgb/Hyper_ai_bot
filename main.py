import asyncio
import json
import websockets


class DerivClient:
    SYMBOLS = {"XAU/USD": "frxXAUUSD", "EUR/USD": "frxEURUSD"}

    def __init__(self, app_id: str = "1089", api_token: str = ""):
        self.app_id = str(app_id).strip() or "1089"
        self.api_token = api_token.strip()
        self.ws_url = "wss://ws.derivws.com/websockets/v3?app_id=" + self.app_id
        self.ws = None
        self.account_info = {}
        self.is_connected = False
        self.is_authorized = False

    async def connect(self) -> dict:
        if not self.api_token:
            raise ValueError("Deriv API Token is required.")
        self.ws = await websockets.connect(self.ws_url, ping_interval=25, ping_timeout=10, close_timeout=5)
        self.is_connected = True
        auth_res = await self._send_and_receive({"authorize": self.api_token})
        if "error" in auth_res:
            await self.disconnect()
            raise ConnectionError(f"Deriv Auth Failed: {auth_res['error']['message']}")
        self.is_authorized = True
        self.account_info = auth_res.get("authorize", {})
        return {
            "loginid": self.account_info.get("loginid", "Unknown"),
            "balance": float(self.account_info.get("balance", 0.0)),
            "currency": self.account_info.get("currency", "USD"),
            "is_virtual": bool(self.account_info.get("is_virtual", 1)),
        }

    async def disconnect(self):
        self.is_connected = False
        self.is_authorized = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

    async def _send_and_receive(self, payload: dict) -> dict:
        if not self.ws or not self.is_connected:
            raise ConnectionError("Not connected to Deriv WebSocket.")
        await self.ws.send(json.dumps(payload))
        raw = await asyncio.wait_for(self.ws.recv(), timeout=15)
        return json.loads(raw)

    async def get_balance(self) -> float:
        res = await self._send_and_receive({"balance": 1})
        if "error" in res:
            raise RuntimeError(res["error"]["message"])
        return float(res["balance"]["balance"])

    async def get_candles(self, pair: str = "XAU/USD", count: int = 300, granularity: int = 300) -> list:
        symbol = self.SYMBOLS.get(pair, pair)
        res = await self._send_and_receive({"ticks_history": symbol, "adjust_start_time": 1, "count": count, "end": "latest", "style": "candles", "granularity": granularity})
        if "error" in res:
            raise RuntimeError(f"Candle Error ({pair}): {res['error']['message']}")
        return res.get("candles", [])

    async def place_multiplier_trade(self, pair: str, direction: str, stake: float, multiplier: int = 100, stop_loss: float = 5.0, take_profit: float = 10.0) -> dict:
        if not self.is_authorized:
            raise PermissionError("Account not authorized.")
        symbol = self.SYMBOLS.get(pair, pair)
        contract_type = "MULTUP" if direction.upper() == "BUY" else "MULTDOWN"
        currency = self.account_info.get("currency", "USD")
        res = await self._send_and_receive({"buy": 1, "price": round(float(stake), 2), "parameters": {"amount": round(float(stake), 2), "basis": "stake", "contract_type": contract_type, "currency": currency, "symbol": symbol, "multiplier": int(multiplier), "limit_order": {"stop_loss": round(float(stop_loss), 2), "take_profit": round(float(take_profit), 2)}}})
        if "error" in res:
            return {"status": "rejected", "reason": res["error"]["message"]}
        buy_data = res.get("buy", {})
        return {"status": "executed", "contract_id": buy_data.get("contract_id"), "pair": pair, "direction": direction.upper(), "buy_price": buy_data.get("buy_price")}
    
