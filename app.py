# encoding: utf-8
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import requests
from decimal import Decimal
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get('LINE_ACCESS_TOKEN', '')) #Your Channel Access Token
handler = WebhookHandler(os.environ.get('LINE_SECRET', '')) #Your Channel Secret

@app.route("/callback", methods=['POST', 'GET'])
def callback():
    if request.method == 'GET':
        return 'Hi'
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text #message from user
    response = ''
    if text.lower() == 'knc':
        response = request_coinmarketcap('kyber-network')
    elif text.lower() == 'eth':
        response = request_coinmarketcap('ethereum')
    elif text.lower() == 'btc':
        response = request_coinmarketcap('bitcoin')
    elif text.lower() == 'bch':
        response = request_coinmarketcap('bitcoin-cash')
    elif text.lower() == 'profit':
        response = calculate_profit()
    elif text.lower() == 'help':
        response = 'Possible commands: [knc, eth, btc, bch, profit]'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)) #reply the same message from user


def handle_coinmarketcap_response(r):
    resp = r.json()[0]
    return 'Symbol: {symbol}\nUSD: ${usd}\nPercent Change 24h: {percent_change}'.format(
        symbol=resp['symbol'],
        usd=resp['price_usd'], 
        percent_change=resp['percent_change_24h']
    )


def request_coinmarketcap(coin):
    return handle_coinmarketcap_response(requests.get('https://api.coinmarketcap.com/v1/ticker/{}/'.format(coin)))


def calculate_profit():
    cost = Decimal('1.5981')
    r = requests.get('https://api.coinmarketcap.com/v1/ticker/kyber-network/')
    price = Decimal(r.json()[0]['price_usd']).quantize(Decimal('1.0000'))
    pl = (price-cost)*100/cost
    sign = '+' if pl > 0 else ''
    pl_in_thb = pl/100 * 120000
    return 'Cost:\t\t ${}\nPrice:\t\t ${}\nP/L:\t\t {}{}%\nP/L(THB):\t {}{}'.format(
        cost, price, sign, pl.quantize(Decimal('1.00')), 
        sign, pl_in_thb.quantize(Decimal('1.00')))


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 80)))
