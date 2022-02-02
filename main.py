import subprocess
import time
from datetime import datetime
import math
import discord
import sqlite3
import os
from dotenv import load_dotenv
from discord.ext import commands
import argparse

# from discord.ext.commands import client


intents = discord.Intents.all()

load_dotenv()
start_time = datetime.today()

rank_map = {
    "l": -1,
    "u": 0,
    "i1": 1,
    "i2": 2,
    "i3": 3,
    "b1": 4,
    "b2": 5,
    "b3": 6,
    "s1": 7,
    "s2": 8,
    "s3": 9,
    "g1": 10,
    "g2": 11,
    "g3": 12,
    "p1": 13,
    "p2": 14,
    "p3": 15,
    "d1": 16,
    "d2": 17,
    "d3": 18,
    "im": 19,
    "r": 20,
}

inv_rank_map = {v: k for k, v in rank_map.items()}

def parity_check(rank):
    if isinstance(rank, str):
        r = rank_map[rank]
    elif isinstance(rank,int):
        r = rank

    if r >= 19:
        return [19,20]
    elif r >= 16:
        return [16,17,18,19,20]
    elif r >= 15:
        return [15, 16,17,18]
    elif r >= 14:
        return [14,15,16,17]
    elif r >= 13:
        return [13,14,15,16]
    elif r >= 10:
        return [10,11,12,13,14,15]
    elif r >= 7:
        return [7,8,9,10,11,12]
    else:
        return [1,2,3,4,5,6,7,8,9]

addparser = argparse.ArgumentParser()
addparser.add_argument("-u","--username")
addparser.add_argument("-p","--password")
addparser.add_argument("-i","--id", nargs='+')
addparser.add_argument("-r","--rank")

client = commands.Bot(command_prefix='!', intents=intents)

con = sqlite3.connect('accounts.db')
cur = con.cursor()
# Create table
try:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS accounts (username CHAR(20), password CHAR(20), riotid CHAR(16), tag CHAR(5), rank INT, last_updated TIMESTAMP , added TIMESTAMP, PRIMARY KEY (username))")
except:
    print("accounts table already exists.")
# Save (commit) the changes
con.commit()


@client.event
async def on_ready():
    global start_time
    print('Logged in as {0.user}'.format(client))
    start_time = datetime.today()


@client.event
async def on_member_join(member):
    if member.guild.id == 935001989727809616:
        sdnrole = member.guild.get_role(935004221844115487)
        await member.add_roles(sdnrole)
        await member.edit(nick="SDN " + member.name)


async def shell(command):
    process = subprocess.Popen(command.split(" "),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode("utf-8")


async def create_status_embed():
    embed = discord.Embed(title="Status", description="Polyfrog is online.", color=0x00d12a)
    embed.set_author(name="Polyfrog")
    embed.set_thumbnail(url=client.user.avatar_url)
    time_delta = (datetime.today() - start_time)
    total_seconds = time_delta.total_seconds()
    days = time_delta.days
    hours = math.floor((total_seconds - days * 24 * 60 * 60) / 3600)
    minutes = math.floor((total_seconds - days * 24 * 60 * 60 - hours * 60 * 60) / 60)
    seconds = math.floor((total_seconds - days * 24 * 60 * 60 - hours * 60 * 60 - minutes * 60))
    embed.add_field(name="Boot Time", value=start_time.isoformat(), inline=False)
    embed.add_field(name="Uptime",
                    value=str(time_delta.days) + ":" + str(hours) + ":" + str(minutes) + ":" + str(seconds),
                    inline=True)
    commits = await shell("git rev-list --all --count")
    embed.add_field(name="Commit", value=commits, inline=True)
    embed.set_footer(text="Data collected since boot. No past data is retained.")
    return embed


@client.command()
async def status(ctx):
    embed = await create_status_embed()
    await ctx.send(embed=embed)


@client.command()
async def ax(ctx, *args):
    account = addparser.parse_args(args)
    now = int(time.time() * 1000)
    if len(args) == 0:
        await ctx.send("USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    elif not account.username or not account.password:
        await ctx.send("Missing username or password. USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    else:
        riotid = None if not account.id else " ".join(account.id).split("#")
        tag  = None if not riotid else riotid[1]
        riotid = None if not riotid else riotid[0]
        account.rank = None if not account.rank else rank_map[account.rank]
        cur.execute(
            'INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',(account.username, account.password, riotid,
                                                                         tag, account.rank,
                                                                         now, now))
        con.commit()

@client.command()
async def add(ctx, *args):
    account = addparser.parse_args(args)
    now = int(time.time() * 1000)
    if len(args) == 0:
        await ctx.send("USAGE: `!add -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    # elif not account.username or not account.password:
    #     await ctx.send("Missing username or password. USAGE: `!add -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    # else:
    #     cur.execute(
    #         'INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)', (args[0], args[1], args[2].split("#")[0],
    #                                                                      args[2].split("#")[1], args[3],
    #                                                                      now, now))
    #     con.commit()


client.run(os.environ["PF_TOKEN"])
