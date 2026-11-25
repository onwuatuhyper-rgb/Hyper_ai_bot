import os
import asyncio
import datetime
import flet as ft
from api.deriv_client import DerivClient
from core.ai_engine import MarketAIModel
from core.risk_manager import RiskManager


class HyperAIBotApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "HYPER AI BOT"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 14
        self.page.scroll = ft.ScrollMode.AUTO
        self.client = None
        self.risk_manager = RiskManager()
        self.models = {"XAU/USD": MarketAIModel("XAU/USD"), "EUR/USD": MarketAIModel("EUR/USD")}
        self.is_running = False

        self.status_badge = ft.Text("DISCONNECTED", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
        self.mode_text = ft.Text("Mode: Not Connected", size=13, color=ft.Colors.GREY_400)
        self.balance_text = ft.Text("$0.00", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        self.xau_text = ft.Text("XAU/USD: Waiting...", size=14)
        self.eur_text = ft.Text("EUR/USD: Waiting...", size=14)
        self.log_list = ft.ListView(height=210, spacing=5, auto_scroll=True)

        self.token_in = ft.TextField(label="Deriv API Token", password=True, can_reveal_password=True)
        self.appid_in = ft.TextField(label="Deriv App ID", value="1089")
        self.stake_in = ft.TextField(label="Stake ($)", value="10.0")
        self.conf_in = ft.TextField(label="Min Confidence (0.50-0.95)", value="0.65")
        self.loss_in = ft.TextField(label="Max Daily Loss ($)", value="30.0")
        self.streak_in = ft.TextField(label="Max Consecutive Losses", value="3")
        self.btn = ft.Button("START AUTO-TRADING", bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=self.toggle_bot)
        self.build_ui()

    def log(self, msg: str, color=ft.Colors.WHITE_70):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_list.controls.append(ft.Text(f"[{ts}] {msg}", size=12, color=color))
        if len(self.log_list.controls) > 60:
            self.log_list.controls.pop(0)
        self.page.update()

    def build_ui(self):
        hdr = ft.Container(padding=12, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=12, content=ft.Row([ft.Column([ft.Text("HYPER AI BOT", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300), self.mode_text]), self.status_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        bal = ft.Container(padding=14, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=12, content=ft.Column([ft.Text("Deriv Balance", size=12, color=ft.Colors.GREY_400), self.balance_text, self.btn]))
        sig = ft.Container(padding=14, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=12, content=ft.Column([ft.Text("AI Signals (5m)", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200), self.xau_text, self.eur_text]))
        logs = ft.Container(padding=14, bgcolor=ft.Colors.GREY_900, border_radius=12, content=ft.Column([ft.Text("Execution Log", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300), self.log_list]))
        cfg = ft.Container(padding=14, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=12, content=ft.Column([self.token_in, self.appid_in, self.stake_in, self.conf_in, self.loss_in, self.streak_in, ft.Button("Connect & Save", on_click=self.connect_deriv)]))
        tabs = ft.Tabs(selected_index=0, expand=True, tabs=[ft.Tab(label="Dashboard", content=ft.Column([bal, sig, logs])), ft.Tab(label="API & Settings", content=ft.Column([cfg]))])
        self.page.add(hdr, tabs)
        self.log("Ready. Enter Deriv API Token in API & Settings.")

    def _set_risk(self):
        self.risk_manager = RiskManager(float(self.conf_in.value or 0.65), float(self.stake_in.value or 10.0), float(self.loss_in.value or 30.0), int(self.streak_in.value or 3))

    async def connect_deriv(self, e):
        try:
            self._set_risk()
            if self.client:
                await self.client.disconnect()
            self.client = DerivClient(self.appid_in.value, self.token_in.value)
            info = await self.client.connect()
            mode = "DEMO" if info["is_virtual"] else "REAL"
            self.status_badge.value, self.status_badge.color = "CONNECTED", ft.Colors.GREEN_400
            self.mode_text.value = f"{mode} | {info['loginid']}"
            self.balance_text.value = f"${info['balance']:,.2f}"
            self.log(f"Connected ({mode}): {info['loginid']}", ft.Colors.GREEN_300)
        except Exception as ex:
            self.status_badge.value, self.status_badge.color = "ERROR", ft.Colors.RED_400
            self.log(f"Auth error: {ex}", ft.Colors.RED_300)
        self.page.update()

    async def toggle_bot(self, e):
        if self.is_running:
            self.is_running = False
            self.btn.text, self.btn.bgcolor = "START AUTO-TRADING", ft.Colors.GREEN_700
            self.log("Stopped.", ft.Colors.AMBER_300)
            self.page.update()
            return
        if not self.client or not self.client.is_authorized:
            await self.connect_deriv(None)
            if not self.client or not self.client.is_authorized:
                return
        self._set_risk()
        self.is_running = True
        self.btn.text, self.btn.bgcolor = "STOP AUTO-TRADING", ft.Colors.RED_700
        self.log("AI engine running...", ft.Colors.CYAN_300)
        self.page.update()
        asyncio.create_task(self._loop())

    async def _loop(self):
        while self.is_running:
            try:
                bal = await self.client.get_balance()
                self.balance_text.value = f"${bal:,.2f}"
                for pair in ("XAU/USD", "EUR/USD"):
                    if not self.is_running:
                        break
                    candles = await self.client.get_candles(pair, 300, 300)
                    p = await asyncio.to_thread(self.models[pair].predict_latest, candles)
                    txt = f"{pair}: {p['signal']} | Conf {p['confidence']:.0%} | Acc {p['unseen_accuracy']:.0%}"
                    if pair == "XAU/USD":
                        self.xau_text.value = txt
                    else:
                        self.eur_text.value = txt
                    self.page.update()
                    d = self.risk_manager.evaluate_trade(p["signal"], p["confidence"], bal)
                    if d["approved"]:
                        res = await self.client.place_multiplier_trade(pair, p["signal"], d["stake"], 100, d["stop_loss"], d["take_profit"])
                        self.log(f"{pair} {res['status']}: {res.get('contract_id', res.get('reason'))}", ft.Colors.GREEN_300)
                    else:
                        self.log(f"{pair} skipped: {d['reason']}", ft.Colors.GREY_400)
                await asyncio.sleep(60)
            except Exception as ex:
                self.log(f"Reconnecting: {ex}", ft.Colors.RED_300)
                await asyncio.sleep(10)


port = int(os.environ.get("PORT", 8080))
os.environ["FLET_SERVER_PORT"] = str(port)
os.environ["FLET_SERVER_IP"] = "0.0.0.0"
ft.run(lambda page: HyperAIBotApp(page), view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
        
