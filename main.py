import subprocess
import time
from datetime import datetime
import math
import discord
import sqlite3
import os

from discord.ext.commands import Context
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
    elif isinstance(rank, int):
        r = rank

    if r >= 19:
        return [19, 20]
    elif r >= 16:
        return [16, 17, 18, 19, 20]
    elif r >= 15:
        return [15, 16, 17, 18]
    elif r >= 14:
        return [14, 15, 16, 17]
    elif r >= 13:
        return [13, 14, 15, 16]
    elif r >= 10:
        return [10, 11, 12, 13, 14, 15]
    elif r >= 7:
        return [7, 8, 9, 10, 11, 12]
    else:
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]


interactions = {}

addparser = argparse.ArgumentParser()
addparser.add_argument("-u", "--username")
addparser.add_argument("-p", "--password")
addparser.add_argument("-i", "--id", nargs='+')
addparser.add_argument("-r", "--rank")

prefix = "!"

client = commands.Bot(command_prefix=prefix, intents=intents)

con = sqlite3.connect('accounts.db')
cur = con.cursor()
# Create table
try:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS accounts (username CHAR(20), password CHAR(20), riotid CHAR(16), tag CHAR(5), rank INT, owner BIGINT, last_updated TIMESTAMP , added TIMESTAMP, PRIMARY KEY (username))")
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
async def status(ctx: Context):
    embed = await create_status_embed()
    await ctx.send(embed=embed)


@client.command()
async def ax(ctx: Context, *args):
    account = addparser.parse_args(args)
    now = int(time.time() * 1000)
    if len(args) == 0:
        await ctx.send("USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    elif not account.username or not account.password:
        await ctx.send(
            "Missing username or password. USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    else:
        riotid = None if not account.id else " ".join(account.id).split("#")
        tag = None if not riotid else riotid[1]
        riotid = None if not riotid else riotid[0]
        account.rank = None if not account.rank else rank_map[account.rank]
        cur.execute(
            'INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)', (account.username, account.password, riotid,
                                                              tag, account.rank, ctx.author.id,
                                                              now, now))
        con.commit()


@client.command()
async def exit(ctx: Context, *args):
    if ctx.author.id not in interactions.keys():
        await ctx.send("No process was occurring.")
        return
    del interactions[ctx.author.id]
    await ctx.send("Process cancelled.")


@client.command()
async def add(ctx: Context, *args):
    if len(args) > 0:
        ax(ctx, args)
    elif ctx.author.id not in interactions.keys():
        interactions[ctx.author.id] = {"fn": "add", "step": 1, "data": []}
        await ctx.send(
            "This command is for adding alt accounts to the database. Anybody who asks to use this account will "
            "require your permission to get the credentials, everytime. However, passwords are stored in plain text. "
            "**Do not add accounts that you care about**. Just follow the prompts, and use !exit if you "
            "want to cancel the process.")
        await ctx.send("Enter your account's Riot username. (Not your RiotID, but your login username)")


@client.event
async def on_message(msg: discord.Message):
    if msg.content.startswith(prefix):
        await client.process_commands(msg)
        return
    if msg.author.id in interactions.keys():
        if interactions[msg.author.id]["fn"] == "add":
            if interactions[msg.author.id]["step"] == 1:
                interactions[msg.author.id]["data"].append(msg.content)
                await msg.channel.send(
                    "What is the login password? This password will be stored in plain text. **Do not add accounts that you care about.**")
                interactions[msg.author.id]["step"] += 1
            elif interactions[msg.author.id]["step"] == 2:
                interactions[msg.author.id]["data"].append(msg.content)
                await msg.channel.send("Type in your Riot ID. Example: SDN Polyfrog#008")
                interactions[msg.author.id]["step"] += 1
            elif interactions[msg.author.id]["step"] == 3:
                interactions[msg.author.id]["data"].append(msg.content)
                await msg.channel.send(
                    "Type in the rank of this account. Example: silver 3"
                    "If it has not reached the level required for competitive, type `locked`"
                    "If it is unranked, type `unranked`"
                     "If it is immortal or radiant, type `immortal` or `radiant`")
                interactions[msg.author.id]["step"] += 1
            elif interactions[msg.author.id]["step"] == 4:
                interactions[msg.author.id]["data"].append(msg.content)
                await msg.channel.send("We have all the information we need! Wait a second while I add your account.")
                username = interactions[msg.author.id]["data"][0]
                password = interactions[msg.author.id]["data"][1]
                riotid = interactions[msg.author.id]["data"][2].split("#")
                tag = None if not riotid else riotid[1]
                riotid = None if not riotid else riotid[0]
                rank = interactions[msg.author.id]["data"][3].lower()
                if rank == "locked":
                    rank = "l"
                elif rank == "unranked":
                    rank = "u"
                elif rank == "immortal":
                    rank = "im"
                elif rank == "radiant":
                    rank = "r"
                else:
                    rank = rank[0] + rank.split(" ")[1]
                rank = rank_map[rank]
                now = int(time.time() * 1000)
                cur.execute(
            'INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)', (username, password, riotid,
                                                              tag, rank, msg.author.id,
                                                              now, now))
            con.commit()
            await msg.channel.send(
            "Done. Your account has been added. Use `!delete " + interactions[msg.author.id]["data"][
                0] + "` to remove this account from the database.")


            client.run(os.environ["PF_TOKEN"])
