import asyncio
import json
import websockets


class DerivClient:
    SYMBOLS = {"XAU/USD": "frxXAUUSD", "EUR/USD": "frxEURUSD"}

    def __init__(self, app_id: str = "1089", api_token: str = ""):
        self.app_id = str(app_id).strip() or "1089"
        self.api_token = api_token.strip()
        host = "://derivws.com"
        path = "/websockets/v3?app_id=" + self.app_id
        self.ws_url = "wss://" + host + path
        self.ws = None
        self.account_info = {}
        self.is_connected = False
        self.is_authorized = False

    async def connect(self) -> dict:
        if not self.api_token:
            raise ValueError("Deriv API Token is required.")
        self.ws = await websockets.connect(self.ws_url)
        self.is_connected = True
        auth = await self._send({"authorize": self.api_token})
        if "error" in auth:
            await self.disconnect()
            raise ConnectionError(auth["error"]["message"])
        self.is_authorized = True
        self.account_info = auth.get("authorize", {})
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
            await self.ws.close()
            self.ws = None

    async def _send(self, payload: dict) -> dict:
        await self.ws.send(json.dumps(payload))
        raw = await asyncio.wait_for(self.ws.recv(), timeout=15)
        return json.loads(raw)

    async def get_balance(self) -> float:
        res = await self._send({"balance": 1})
        return float(res["balance"]["balance"])

    async def get_candles(self, pair: str = "XAU/USD", count: int = 300, granularity: int = 300) -> list:
        sym = self.SYMBOLS.get(pair, pair)
        res = await self._send({"ticks_history": sym, "adjust_start_time": 1, "count": count, "end": "latest", "style": "candles", "granularity": granularity})
        if "error" in res:
            raise RuntimeError(res["error"]["message"])
        return res.get("candles", [])

    async def place_multiplier_trade(self, pair: str, direction: str, stake: float, multiplier: int = 100, stop_loss: float = 5.0, take_profit: float = 10.0) -> dict:
        sym = self.SYMBOLS.get(pair, pair)
        ctype = "MULTUP" if direction.upper() == "BUY" else "MULTDOWN"
        cur = self.account_info.get("currency", "USD")
        params = {"amount": round(float(stake), 2), "basis": "stake", "contract_type": ctype, "currency": cur, "symbol": sym, "multiplier": int(multiplier), "limit_order": {"stop_loss": round(float(stop_loss), 2), "take_profit": round(float(take_profit), 2)}}
        res = await self._send({"buy": 1, "price": round(float(stake), 2), "parameters": params})
        if "error" in res:
            return {"status": "rejected", "reason": res["error"]["message"]}
        b = res.get("buy", {})
        return {"status": "executed", "contract_id": b.get("contract_id"), "pair": pair, "direction": direction.upper()}
            
