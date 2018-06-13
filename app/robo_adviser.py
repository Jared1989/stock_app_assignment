import csv
from dotenv import load_dotenv
import json
import os
import pdb
import requests
from datetime import datetime

def parse_response(response_text):
    # response_text can be either a raw JSON string or an already-converted dictionary
    if isinstance(response_text, str): # if not yet converted, then:
        response_text = json.loads(response_text) # convert string to dictionary

    results = []
    time_series_daily = response_text["Time Series (Daily)"] #> a nested dictionary
    for trading_date in time_series_daily: # FYI: can loop through a dictionary's top-level keys/attributes
        prices = time_series_daily[trading_date] #> {'1. open': '101.0924', '2. high': '101.9500', '3. low': '100.5400', '4. close': '101.6300', '5. volume': '22165128'}
        result = {
            "date": trading_date,
            "open": prices["1. open"],
            "high": prices["2. high"],
            "low": prices["3. low"],
            "close": prices["4. close"],
            "volume": prices["5. volume"]
        }
        results.append(result)
    return results

def write_prices_to_file(prices=[], filename="db/prices.csv"):
    csv_filepath = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(csv_filepath, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for d in prices:
            row = {
                "timestamp": d["date"], # change attribute name to match project requirements
                "open": d["open"],
                "high": d["high"],
                "low": d["low"],
                "close": d["close"],
                "volume": d["volume"]
            }
            writer.writerow(row)

def get_symbol():
    symbol = input("Please enter one or more stock symbols separated by commas (e.g. NFLX, MSFT, GOOG, AAPL) or DONE to quit: ")
    symbol = symbol.split(", ")

    # VALIDATE SYMBOL AND PREVENT UNECESSARY REQUESTS
    spot = 0
    for s in symbol:
        while True:
            try:
                float(s)
                s = input("Oh, invalid stock symbol " + s + ". expecting a properly-formed stock symbol like 'MSFT'. Please try again: ")
                symbol[spot] = s
            except ValueError as e:
                pass
                break
        spot += 1

    spot = 0
    for s in symbol:
        while len(s) > 5:
            s = input("Oh, invalid stock symbol " + s + ". expecting a properly-formed stock symbol like 'MSFT'. Please try again: ")
            symbol[spot] = s
        spot += 1
    return symbol

def get_calc(symbol, daily_prices):

   # PERFORM CALCULATIONS
    now = datetime.now()

    latest_close = datetime.strptime(daily_prices[0]["date"], '%Y-%m-%d').strftime('%B %d, %Y')

    print("-------------------------------")
    print(f"Stock: {symbol}")
    print(now.strftime("Run at %I:%M%p on %B %d, %Y"))
    print(f"Latest Data From: {latest_close}")

    latest_closing_price = daily_prices[0]["close"]
    latest_closing_price = float(latest_closing_price)
    latest_closing_price_usd = "${0:,.2f}".format(latest_closing_price)
    print(f"Latest Closing Price: {latest_closing_price_usd}")

    recent_100_highs = [float(daily_price["high"]) for daily_price in daily_prices[0:100]]
    average_recent_100_highs = sum(recent_100_highs)/len(recent_100_highs)
    average_recent_100_highs_usd = "${0:,.2f}".format(average_recent_100_highs)
    print(f"Recent Average High: {average_recent_100_highs_usd}")

    recent_100_lows = [float(daily_price["low"]) for daily_price in daily_prices[0:100]]
    average_recent_100_lows = sum(recent_100_lows)/len(recent_100_lows)
    average_recent_100_lows_usd = "${0:,.2f}".format(average_recent_100_lows)
    print(f"Recent Average Low: {average_recent_100_lows_usd}")

    the_52_week_highs = [float(daily_price["high"]) for daily_price in daily_prices[0:252]]
    max_52_week_high = max(the_52_week_highs)
    max_52_week_high_usd = "${0:,.2f}".format(max_52_week_high)
    print(f"The 52 Week High: {max_52_week_high_usd}")

    the_52_week_lows = [float(daily_price["low"]) for daily_price in daily_prices[0:252]]
    min_52_week_low = min(the_52_week_lows)
    min_52_week_low_usd = "${0:,.2f}".format(min_52_week_low)
    print(f"The 52 Week Low: {min_52_week_low_usd}")


    buy_point = 1.2 * average_recent_100_lows
    buy_point_usd = "${0:,.2f}".format(buy_point)
    if latest_closing_price < buy_point:
        print(f"Recommendation For {symbol}: BUY! The stock's latest closing price is below our target stock price of {buy_point_usd}")
    else:
        print(f"Recommendation For {symbol}: DON'T BUY! The stock's latest closing price is above our target stock price of {buy_point_usd}")
    print("-------------------------------")


def get_stock(stock, NoStocks):
    advkey = os.environ.get("ALPHAVANTAGE_API_KEY")
    request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock}&apikey={advkey}&outputsize=full"
    # ISSUE "GET" REQUEST
    response = requests.get(request_url)
    response_body = json.loads(response.text)
    if "Error Message" in response.text:
        print("Sorry, couldn't find any trading data for that stock symbol.  Please try again!")
    else:
        # PARSE RESPONSE (AS LONG AS THERE ARE NO ERRORS)
        daily_prices = parse_response(response.text)
        # WRITE TO CSV
        if NoStocks != 1:
            NameFile = "_" + stock
        else:
            NameFile = ""

        write_prices_to_file(prices=daily_prices, filename="db/prices" + NameFile + ".csv")
        get_calc(stock, daily_prices)

if __name__ == '__main__': # only execute if file invoked from the command-line, not when imported into other files, like tests

    load_dotenv() # loads environment variables set in a ".env" file, including the value of the ALPHAVANTAGE_API_KEY variable

    #api_key = os.environ.get("ALPHAVANTAGE_API_KEY") or "OOPS. Please set an environment variable named 'ALPHAVANTAGE_API_KEY'."

    # CAPTURE USER INPUTS (SYMBOL)

    symbols = []
    symbols = get_symbol()
    while symbols[0].upper() != "DONE":
        for s in symbols:
            get_stock(s, len(symbols))
        symbols = get_symbol()

# CREDITS:
# Python Programming Third Edition, Michael Dawson; slicing a list
# https://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
# https://en.wikipedia.org/wiki/Trading_day trading days in 52 weeks
# https://www.tutorialspoint.com/python/string_split.htm
# https://docs.python.org/2/library/string.html
# https://github.com/s2t2/stocks-app-py-2018
