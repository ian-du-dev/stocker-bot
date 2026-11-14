import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import yfinance as yf
import json
import random

"""
const
STARTBALANCE
const
MAX_WORK
const
MIN_WORK
const
TOKEN
const
handler
const
intents
const
bot
const
BANK_FILE
"""

STARTBALANCE = 100
MAX_WORK = 25
MIN_WORK = 5

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

BANK_FILE = "bank.json"

def loadbank():
    if not os.path.exists(BANK_FILE):
        return {}
    try:
        with open(BANK_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("corrupted json file")
        return {}

def savebank(data):
    with open(BANK_FILE, "w") as f:
        json.dump(data, f)

def start(username):
    bank = loadbank()
    if username not in bank:
        bank[username] = {"balance": STARTBALANCE}
        savebank(bank)

@bot.event
async def on_ready():
    print(f"Ready as {bot.user.name}")



#BALANCE
@bot.command(
        name="balance",
        help="Shows how much 💵 you have."
)
async def balance(ctx):

    bank = loadbank()
    username = ctx.author.name

    if username in bank:
        await ctx.reply(f"{ctx.author.mention}'s balance is 💵{bank[username]['balance']}.")

        stocks = [f"{ticker}: {amount}" for ticker, amount in bank[username].items() if ticker != "balance"]

        if stocks:
            await ctx.reply (f"{ctx.author.mention} owns these stocks: " + ", ".join(stocks))

    else:
        start(username)
        await ctx.reply(f"Welcome, {ctx.author.mention}! Your starting balance is 💵{STARTBALANCE}.")



#WORK
@bot.command(
        name="work",
        help="Earns you some 💵."
)
@commands.cooldown(1, 600, commands.BucketType.user)
async def work(ctx):

    username = ctx.author.name
    bank = loadbank()
    earned = random.randint(MIN_WORK, MAX_WORK)

    if username not in bank:
        start(username)
        bank = loadbank()
        await ctx.reply(f"Welcome, {ctx.author.mention}! Your starting balance is 💵{STARTBALANCE}.")
    
    bank[username]["balance"] += earned
    savebank(bank)

    await ctx.reply(f"{ctx.author.mention} earned 💵{earned}.")

@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"{ctx.author.mention}, wait for {int(error.retry_after)} seconds.")



#PAY
@bot.command(
        name="pay",
        help="Gives someone else your 💵."
)
async def pay(ctx, receivername, amount):
    
    try:
        amount = float(amount)
    except ValueError:
        await ctx.reply("Amount must be a positive number.")
        return
    
    if amount <= 0:
        await ctx.reply("Amount must be a positive number.")
        return
    
    receiver = discord.utils.find(lambda m: m.name == receivername, ctx.guild.members)
    
    if not receiver:
        await ctx.reply(f'Username "{receivername}" not found in server.')
        return
    
    payername = ctx.author.name

    bank = loadbank()

    if payername not in bank:
        start(payername)
    
    if receivername not in bank:
        start(receivername)
    
    bank = loadbank()

    if bank[payername].get("balance", 0) >= amount:
        bank[payername]["balance"] = round(bank[payername].get("balance", 0) - amount, 2)
        bank[receivername]["balance"] = round(bank[receivername].get("balance", 0) + amount, 2)
        savebank(bank)

        await ctx.reply(f"{ctx.author.mention} paid 💵{amount} to {receivername}.")

    else:
        await ctx.reply(f"{ctx.author.mention} doesn't have enough 💵.")



#ADDMONEY
@bot.command(
        name="addmoney",
        help="Admin command to add 💵."
)
async def addmoney(ctx):
    ctx.reply("cmd in development")



#REMOVEMONEY
@bot.command(
        name="removemoney",
        help="Admin command to remove 💵."
)
async def removemoney(ctx):
    ctx.reply("cmd in development")



#BUYSTOCK
@bot.command(
        name="buystock",
        help="Buys some stocks using 💵."
)
async def buystock(ctx, ticker, amount):

    try:
        amount = float(amount)
    except ValueError:
        await ctx.reply("Amount must be a positive number.")
        return
    
    if amount <= 0:
        await ctx.reply("Amount must be a positive number.")
        return
    
    bank = loadbank()
    username = ctx.author.name
    ticker = str(ticker).upper()

    if username not in bank:
        start(username)
        bank = loadbank()
        await ctx.reply(f"Welcome, {ctx.author.mention}! Your starting balance is 💵{STARTBALANCE}.")

    try:
        price = round(yf.Ticker(ticker).history(period="1d")["Close"].iloc[0], 2)
    except IndexError:
        await ctx.reply("No data found on given ticker, possibly delisted.")
        return
    
    if price * amount <= bank[username]["balance"]:
        bank[username]["balance"] = round(bank[username].get("balance", 0) - (price * amount), 2)
        bank[username][ticker] = round(bank[username].get(ticker, 0) + amount, 4)
        savebank(bank)

        await ctx.reply(f"{ctx.author.mention} bought {amount} shares of {ticker} at ${price} per share. Total purchase: 💵{round(price * amount, 2)}.")
    
    else:
        await ctx.reply(f"{ctx.author.mention} doesn't have enough 💵.")



#SELLSTOCK
@bot.command(
        name="sellstock",
        help="Sells some stocks earning 💵."
)
async def sellstock(ctx, ticker, amount):

    try:
        if amount != "all":
            amount = float(amount)

            if amount <= 0:
                await ctx.reply('Amount must be a positive number, or "all".')
                return
            
    except ValueError:
        await ctx.reply('Amount must be a positive number, or "all".')
        return
    
    bank = loadbank()
    username = ctx.author.name
    ticker = str(ticker).upper()

    if username not in bank:
        start(username)
        bank = loadbank()
        await ctx.reply(f"Welcome, {ctx.author.mention}! Your starting balance is 💵{STARTBALANCE}.")
        await ctx.reply("error")

    if ticker not in bank[username]:
        await ctx.reply(f"{ctx.author.mention} does not own any shares of {ticker}.")
        return
    
    try:
        price = round(yf.Ticker(ticker).history(period="1d")["Close"].iloc[0], 2)
    except IndexError:
        await ctx.reply("No data found on given ticker, possibly delisted.")
        return
    
    if amount == "all":
        amount = bank[username][ticker]

    if amount <= bank[username][ticker]:
        bank[username][ticker] = round(bank[username].get(ticker, 0) - amount, 4)

        if bank[username][ticker] <= 0:
            del bank[username][ticker]

        earned = round(price * amount, 2)
        bank[username]["balance"] = round(bank[username].get("balance", 0) + earned, 2)
        savebank(bank)
        
        await ctx.reply(f"{ctx.author.mention} sold {amount} shares of {ticker} at ${price} per share. Total earned: 💵{earned}.")
    
    else:
        await ctx.reply(f"{ctx.author.mention} doesn't have enough shares of {ticker}.")



#PRICE
@bot.command(
        name="price",
        help="Shows the current price of a stock."
)
async def price(ctx, ticker: str):

    try:
        price = round(yf.Ticker(ticker).history(period="1d")["Close"].iloc[0], 2)
    except IndexError:
        await ctx.reply("No data found on given ticker, possibly delisted.")
        return
    
    await ctx.reply(f"Current stock price of {ticker.upper()}: ${price}")



bot.run(TOKEN=TOKEN, log_handler=handler, log_level=logging.DEBUG)
