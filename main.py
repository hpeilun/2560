from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import Clock

import matplotlib.pyplot as plt
import requests
import math

# ========= 技術指標 =========
def ema(data, period):
    k = 2 / (period + 1)
    ema_vals = []
    for i, v in enumerate(data):
        if i == 0:
            ema_vals.append(v)
        else:
            ema_vals.append(v * k + ema_vals[-1] * (1 - k))
    return ema_vals

def rsi(data, period=14):
    gains, losses = [], []
    rsis = [50]
    for i in range(1, len(data)):
        diff = data[i] - data[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

        if i >= period:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsis.append(100 - (100 / (1 + rs)))
        else:
            rsis.append(50)
    return rsis

# ========= 資料來源 =========
def get_crypto(symbol="BTCUSDT", limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}"
    data = requests.get(url).json()
    close = [float(d[4]) for d in data]
    return close

# ========= 2560 戰法 =========
def strategy_2560(close):
    ema5 = ema(close, 5)
    ema25 = ema(close, 25)
    ema60 = ema(close, 60)

    buy = []
    sell = []

    for i in range(2, len(close)):
        # 關鍵 K：EMA5 上穿 EMA60，且前三根收盤 > EMA25
        if (
            ema5[i - 1] < ema60[i - 1]
            and ema5[i] > ema60[i]
            and close[i - 1] > ema25[i - 1]
            and close[i - 2] > ema25[i - 2]
        ):
            buy.append(i)
        if ema5[i - 1] > ema60[i - 1] and ema5[i] < ema60[i]:
            sell.append(i)

    return buy, sell, ema5, ema25, ema60

# ========= Kivy UI =========
class Chart(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasKivyAgg(self.fig)
        self.add_widget(self.canvas)
        Clock.schedule_once(self.draw, 1)

    def draw(self, *args):
        close = get_crypto()
        buy, sell, ema5, ema25, ema60 = strategy_2560(close)
        r = rsi(close)

        self.ax.clear()
        self.ax.plot(close, label="Price", color="black")
        self.ax.plot(ema5, label="EMA5")
        self.ax.plot(ema25, label="EMA25")
        self.ax.plot(ema60, label="EMA60")

        for i in buy:
            self.ax.scatter(i, close[i], marker="^", color="green")
        for i in sell:
            self.ax.scatter(i, close[i], marker="v", color="red")

        self.ax.legend()
        self.canvas.draw()

class StrategyApp(App):
    def build(self):
        return Chart()

if __name__ == "__main__":
    StrategyApp().run()
