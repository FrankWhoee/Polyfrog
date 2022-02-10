import argparse
import asyncio
import math
import os
import sqlite3
import subprocess
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
import discord
from discord import Reaction, User
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from threading import Timer

# from discord.ext.commands import client


intents = discord.Intents.all()

load_dotenv()
start_time = datetime.today()

rank_map = {
    "lo": -1,
    "un": 0,
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
    "ra": 20,
}

inv_rank_map = {v: k for k, v in rank_map.items()}


def disparity_check(rank):
    if isinstance(rank, str):
        r = rank_map[rank]
    elif isinstance(rank, int):
        r = rank

    disparity_map = [
        [19, 20], [16, 17, 18, 19, 20], [15, 16, 17, 18], [14, 15, 16, 17], [13, 14, 15, 16], [10, 11, 12, 13, 14, 15],
        [7, 8, 9, 10, 11, 12], [1, 2, 3, 4, 5, 6, 7, 8, 9]
    ]

    for d in disparity_map[::-1]:
        if r in d:
            return d


interactions = {}

addparser = argparse.ArgumentParser()
addparser.add_argument("-u", "--username")
addparser.add_argument("-p", "--password")
addparser.add_argument("-i", "--id", nargs='+')
addparser.add_argument("-r", "--rank")

prefix = "!"

client = commands.Bot(command_prefix=prefix, intents=intents)
client.remove_command('help')
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

sdnguild = None
emojis = None
emoji_map = {}

wordle_role_id = 941263746674884648
sdn_role_id = 935004221844115487
sdn_guild_id = 935001989727809616
wordle_spoiler_id = 941264133695873034
wordle_role = None

loop = asyncio.get_event_loop()

def seconds_till_midnight(current_time):
    """
    :param current_time: Datetime.datetime
    :return time till midnight in seconds:
    """
    # Add 1 day to the current datetime, which will give us some time tomorrow
    # Now set all the time values of tomorrow's datetime value to zero,
    # which gives us midnight tonight
    midnight = (current_time + timedelta(days=1)).replace(hour=0, minute=0, microsecond=0, second=0)
    # Subtracting 2 datetime values returns a timedelta
    # now we can return the total amount of seconds till midnight
    return (midnight - current_time).seconds


@client.event
async def on_ready():
    global wordle_role
    global start_time
    global sdnguild
    global emojis
    print('Logged in as {0.user}'.format(client))
    start_time = datetime.today()
    sdnguild = client.get_guild(935001989727809616)
    wordle_role = sdnguild.get_role(wordle_role_id)
    emojis = await sdnguild.fetch_emojis()
    for e in emojis:
        emoji_map[e.name] = e

    timer = Timer(seconds_till_midnight(datetime.now()), run_clear)
    timer.start()
    await client.change_presence(activity=discord.Activity(name="joinsdn.com", type=discord.ActivityType.watching))

async def clear_wordle_roles():
    async for m in sdnguild.fetch_members():
        if wordle_role in m.roles:
            await m.remove_roles(wordle_role)
    timer = Timer(seconds_till_midnight(datetime.now()), run_clear)
    timer.start()


def run_clear():
    asyncio.run_coroutine_threadsafe(clear_wordle_roles(), loop)



@client.event
async def on_member_join(member):
    if member.guild.id == sdn_guild_id:
        sdnrole = member.guild.get_role(sdn_role_id)
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


async def create_account_embed(info, show_password=False):
    if len(info) == 1:
        info = info[0]
    if len(info) == 0:
        embed = discord.Embed(title="No account matches this username", description="", color=0xff0000)
    else:
        embed = discord.Embed(title=info[2] + "#" + info[3], description="", color=0x00ff00)
        owner = await client.fetch_user(info[5])
        embed.set_author(name=owner.name)
        embed.set_thumbnail(url=owner.avatar_url)
        added = datetime.fromtimestamp(info[6])
        last_updated = datetime.fromtimestamp(info[7])

        embed.add_field(name="Username", value=info[0], inline=True)
        if show_password:
            embed.add_field(name="Password", value=info[1], inline=True)
        embed.add_field(name="Rank", value=emoji_map[inv_rank_map[info[4]]], inline=True)
        embed.add_field(name="Last updated", value=str(last_updated), inline=True)
        embed.set_footer(text="Account added on " + str(added))
    return embed


@client.command()
async def status(ctx: Context):
    embed = await create_status_embed()
    await ctx.send(embed=embed)


@client.command()
async def help(ctx: Context):
    embed = discord.Embed(title="Polyfrog Commands",
                          description="Use commands without arguments to get more help details", color=0x00d12a)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="!add", value="Add account.", inline=True)
    embed.add_field(name="!delete `USERNAME`", value="Delete account.", inline=True)
    embed.add_field(name="!get `RANK`", value="Get an account that can play with RANK.", inline=True)
    embed.add_field(name="!update `USERNAME`",
                    value="Update a particular attribute of your account matched with `USERNAME`", inline=True)
    embed.add_field(name="!mine", value="Check what accounts you have.", inline=True)
    embed.add_field(name="!view `USERNAME`", value="Look at the details for one particular account.", inline=True)
    embed.add_field(name="!inspect `USERNAME`", value="DMs you account details **with password**.", inline=True)

    await ctx.send(embed=embed)


@client.command()
async def ax(ctx: Context, *args):
    account = addparser.parse_args(args)
    now = int(time.time())
    if len(args) == 0:
        await ctx.send(
            "USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`\nUse !add without arguments"
            " for interactive guide.")
    elif not account.username or not account.password:
        await ctx.send(
            "Missing username or password. USAGE: `!ax -u USERNAME -p PASSWORD -i RIOTID#TAG(optional) -r RANK(optional)`")
    else:
        cur.execute("SELECT * FROM accounts WHERE username=?", (account.username,))
        output = cur.fetchall()
        if len(output) > 0:
            if output[0][5] == ctx.author.id:
                interactions[ctx.author.id]["update"] = True
                prompt = await ctx.channel.send(
                    "This account already exists in the database. Use `!add` without arguments to update the account.")
                return
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
async def update(ctx: Context, *args):
    if ctx.author.id in interactions.keys():
        await ctx.send("You currently have an ongoing interaction, please use `!exit` to stop it.")
        return
    if len(args) != 1:
        await ctx.send("USAGE: `!update USERNAME`")
        return
    cur.execute("SELECT * FROM accounts WHERE username=?", (args[0],))
    output = cur.fetchall()
    if len(output) > 0:
        if output[0][5] == ctx.author.id:
            prompt = await ctx.send("What would you like to update?\n"
                                    "1. Password\n"
                                    "2. RiotID\n"
                                    "3. Rank\n"
                                    "4. Owner\n"
                                    "*Use !exit to cancel this interaction*")
            await prompt.add_reaction("1️⃣")
            await prompt.add_reaction("2️⃣")
            await prompt.add_reaction("3️⃣")
            await prompt.add_reaction("4️⃣")
            interactions[ctx.author.id] = {"fn": "update", "step": 1, "data": [], "messages": [],
                                           "react_message": prompt,
                                           "username": args[0]}
            interactions[ctx.author.id]["messages"].append(prompt)
        else:
            embed = discord.Embed(title="You do not have permission to inspect this account.", color=0xff0000)
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="No account found with this username.", color=0xff0000)
        await ctx.send(embed=embed)


@client.command()
async def add(ctx: Context, *args):
    if len(args) > 0:
        ax(ctx, args)
    elif ctx.author.id not in interactions.keys():
        interactions[ctx.author.id] = {"fn": "add", "step": 1, "data": [], "messages": [], "update": False}
        embed = discord.Embed(title="!add",
                              description="This command is for adding alt accounts to the database. Anybody who asks to use this account will "
                                          "require your permission to get the credentials, everytime. However, passwords are stored in plain text. "
                                          "**Do not add accounts that you care about**. Just follow the prompts, and use !exit if you "
                                          "want to cancel the process.", color=0x00d12a)
        await ctx.author.send(embed=embed)
        prompt = await ctx.author.send("Enter your account's Riot username. (Not your RiotID, but your login username)")
        interactions[ctx.author.id]["messages"].append(prompt)
    else:
        await ctx.send("You currently have an ongoing interaction, please use `!exit` to stop it.")


@client.command()
async def exit(ctx: Context):
    if ctx.author.id not in interactions.keys():
        await ctx.send("No process was occurring.")
        return
    del interactions[ctx.author.id]
    await ctx.send("Process cancelled.")


@client.command()
async def get(ctx: Context, *args):
    if len(args) == 0 or (len(args) == 1 and args[0] not in ["unrated", "locked", "radiant", "immortal"]):
        await ctx.send(
            "Request for an account that can play with the inputted rank. \nUSAGE: `!get HIGHEST_RANK_IN_PARTY`\nEXAMPLE: `!get silver 3`")
        return
    rank = extract_rank(" ".join(args))
    if rank not in rank_map.keys():
        prompt = await ctx.channel.send(
            "Invalid rank received. Please type in the rank with a space between the league and division. Example: silver 3")
        return
    range = disparity_check(rank)
    rank = rank_map[rank]
    cur.execute("SELECT * FROM accounts WHERE rank BETWEEN ? AND ?", (range[0], range[-1]))
    output = cur.fetchall()
    if len(output) == 0:
        embed = discord.Embed(title="No accounts were found that can play with your selected rank.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    else:
        closest_rank = output[0]
        for info in output:
            if abs(info[4] - rank) < closest_rank[4]:
                closest_rank = info

        apmsg = await ctx.channel.send("Account found. Waiting for approval...")

        owner = await client.fetch_user(closest_rank[5])
        if owner.id == ctx.author.id:
            await owner.send("Since this is your account, no approval is required.",
                             embed=await create_account_embed(closest_rank, show_password=True))
            await apmsg.delete()
        else:
            await owner.send(ctx.author.mention + " is requesting to use the following account:")
            await owner.send(embed=await create_account_embed(closest_rank))
            message = await owner.send("React with ✅ to approve and ❌ to deny this request.")
            interactions[closest_rank[5]] = {"fn": "reqapproval", "account": closest_rank, "ctx": ctx,
                                             "react_message": message, "apmsg": apmsg}
            await message.add_reaction("✅")
            await message.add_reaction("❌")


@client.command()
async def mine(ctx: Context):
    cur.execute("SELECT * FROM accounts WHERE owner=?", (ctx.author.id,))
    output = cur.fetchall()
    if len(output) == 0:
        embed = discord.Embed(title="You don't have any accounts.", color=0x00ff00)
        await ctx.send(embed=embed)
        return
    else:
        description = ""
        for acc in output:
            description += str(emoji_map[inv_rank_map[acc[4]]]) + " " + acc[2] + "#" + acc[3] + "　•　" + acc[0] + "\n"

        embed = discord.Embed(title="Your accounts", description=description, color=0x00d12a)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


@client.command()
async def delete(ctx: Context, username):
    cur.execute("SELECT * FROM accounts WHERE username=?", (username,))
    output = cur.fetchall()
    if len(output) > 0:
        if output[0][5] == ctx.author.id:
            cur.execute("DELETE FROM accounts WHERE username=?", (username,))
            embed = discord.Embed(title="Account deleted succesfully.", color=0x00ff00)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="You do not have permission to delete this account.", color=0xff0000)
            await ctx.send(embed=embed)


@client.command()
async def view(ctx: Context, username):
    cur.execute("SELECT * FROM accounts WHERE username=?", (username,))
    output = cur.fetchall()
    embed = await create_account_embed(output)
    await ctx.send(embed=embed)


@client.command()
async def inspect(ctx: Context, username):
    cur.execute("SELECT * FROM accounts WHERE username=?", (username,))
    output = cur.fetchall()
    if len(output) > 0:
        if output[0][5] == ctx.author.id:
            embed = await create_account_embed(output, show_password=True)
            await ctx.author.send(embed=embed)
        else:
            embed = discord.Embed(title="You do not have permission to inspect this account.", color=0xff0000)
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="No account found with this username.", color=0xff0000)
        await ctx.send(embed=embed)


@client.event
async def on_message(msg: discord.Message):
    if msg.content.startswith(prefix):
        await client.process_commands(msg)
        return
    elif msg.content.startswith("Wordle"):
        await msg.delete()
        await msg.guild.get_channel(wordle_spoiler_id).send(msg.author.mention + "\n" + msg.content)
        await msg.author.add_roles(wordle_role)
    if msg.author.id in interactions.keys():
        intobj = interactions[msg.author.id]
        if intobj["fn"] == "add" and msg.channel.recipient == msg.author:
            intobj["messages"].append(msg)
            while len(intobj["messages"]) > 0:
                m = intobj["messages"].pop()
                try:
                    await m.delete()
                except:
                    continue
            if intobj["step"] == 1:
                cur.execute("SELECT * FROM accounts WHERE username=?", (msg.content,))
                output = cur.fetchall()
                if len(output) > 0:
                    if output[0][5] == msg.author.id:
                        intobj["update"] = True
                        prompt = await msg.channel.send(
                            "This account already exists in the database. Use `!exit` to cancel this transaction, or continue to update this account's information.")
                    else:
                        prompt = await msg.channel.send(
                            "This account already exists in the database. You do not own this account, and can not update it. Transaction cancelled.")
                        del intobj
                        return
                    intobj["messages"].append(prompt)
                intobj["data"].append(msg.content)

                prompt = await msg.channel.send(
                    "What is the login password? This password will be stored in plain text. **Do not add accounts that you care about.**")
                intobj["messages"].append(prompt)
                intobj["step"] += 1
            elif intobj["step"] == 2:
                intobj["data"].append(msg.content)
                prompt = await msg.channel.send("Type in your Riot ID. Example: SDN Polyfrog#008")
                intobj["step"] += 1
                intobj["messages"].append(prompt)
            elif intobj["step"] == 3:
                if "#" not in msg.content:
                    prompt = await msg.channel.send(
                        "Riot ID requires a #. Please retype your Riot ID. Example: SDN Polyfrog#008")
                    return
                    interactions[msg.author.id]["messages"].append(prompt)
                if len(msg.content.split("#")[0]) > 16 or len(msg.content.split("#")[1]) > 5:
                    prompt = await msg.channel.send(
                        "Riot ID requires the name to be 16 characters at most and the tag to be 5 characters at most. Please retype your Riot ID. Example: SDN Polyfrog#008")
                    return
                    interactions[msg.author.id]["messages"].append(prompt)
                intobj["data"].append(msg.content)
                prompt = await msg.channel.send(
                    "Type in the rank of this account. Example: silver 3\n"
                    "If it has not reached the level required for competitive, type `locked`\n"
                    "If it is unranked, type `unranked`\n"
                    "If it is immortal or radiant, type `immortal` or `radiant`\n")
                intobj["messages"].append(prompt)
                intobj["step"] += 1
            elif intobj["step"] == 4:
                rank = extract_rank(msg)
                if rank not in rank_map.keys():
                    prompt = await msg.channel.send(
                        "Invalid rank received. Please type in the rank with a space between the league and division. Example: silver 3")
                    intobj["messages"].append(prompt)
                    return
                prompt = await msg.channel.send(
                    "We have all the information we need! Wait a second while I add your account.")
                intobj["messages"].append(prompt)
                username = intobj["data"][0]
                password = intobj["data"][1]
                riotid = intobj["data"][2].split("#")
                tag = None if not riotid else riotid[1]
                riotid = None if not riotid else riotid[0]
                rank = rank_map[rank]
                now = int(time.time())
                if intobj["update"]:
                    cur.execute(
                        'UPDATE accounts SET password=?, riotid=?, tag=?, rank=?, last_updated=? WHERE username = ?',
                        (password, riotid,
                         tag, rank, now, username))
                    con.commit()
                    prompt = await msg.channel.send(
                        "Done. Your account has been updated. Use `!delete " + intobj["data"][
                            0] + "` to remove this account from the database.")
                    intobj["messages"].append(prompt)
                else:
                    cur.execute(
                        'INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)', (username, password, riotid,
                                                                          tag, rank, msg.author.id,
                                                                          now, now))
                    con.commit()
                    prompt = await msg.channel.send(
                        "Done. Your account has been added. Use `!delete " + intobj["data"][
                            0] + "` to remove this account from the database.")
                    intobj["messages"].append(prompt)
                await view(msg.channel, username)
                del interactions[msg.author.id]
        if intobj["fn"] == "update" and msg.channel == intobj["react_message"].channel and intobj["step"] == 2:
            now = int(time.time())
            if intobj["choice"] == "riotid":
                cur.execute(
                    'UPDATE accounts SET riotid=?, tag=?, last_updated=? WHERE username = ?',
                    (msg.content.split("#")[0], msg.content.split("#")[1], now, intobj["username"]))
            elif intobj["choice"] == "owner":
                cur.execute(
                    'UPDATE accounts SET owner=?, last_updated=? WHERE username = ?',
                    (msg.author.id, now, intobj["username"]))
            elif intobj["choice"] == "rank":
                cur.execute(
                    'UPDATE accounts SET rank=?, last_updated=? WHERE username = ?',
                    (rank_map[extract_rank(msg.content)], now, intobj["username"]))
            else:
                cur.execute(
                    'UPDATE accounts SET ?=?, last_updated=? WHERE username = ?',
                    (intobj["choice"], msg.content, now, intobj["username"]))
            con.commit()
            for i in intobj["messages"]:
                await i.delete()
            await msg.delete()


@client.event
async def on_reaction_add(reaction, user):
    if user.id in interactions and interactions[user.id]["react_message"].id == reaction.message.id:
        intobj = interactions[user.id]
        if intobj["fn"] == "reqapproval":
            if reaction.emoji == "✅":
                await intobj["ctx"].author.send("Your request was approved. Here are the account details:")
                await intobj["ctx"].author.send(embed=await create_account_embed(intobj["account"], show_password=True))
            elif reaction.emoji == "❌":
                await intobj["ctx"].author.send("Your request was denied.")
            await intobj["apmsg"].delete()
            del interactions[user.id]
        if intobj["fn"] == "update" and intobj["step"] == 1:
            channel = intobj["react_message"].channel
            if reaction.emoji == "1️⃣":
                prompt = await channel.send("Please enter the new password:")
                intobj["choice"] = "password"
            elif reaction.emoji == "2️⃣":
                prompt = await channel.send("Please enter the new Riot ID (NAME#TAG):")
                intobj["choice"] = "riotid"
            elif reaction.emoji == "3️⃣":
                prompt = await channel.send("Please enter the new rank:")
                intobj["choice"] = "rank"
            elif reaction.emoji == "4️⃣":
                prompt = await channel.send("Please tag the new owner:")
                intobj["choice"] = "owner"
            intobj["messages"].append(prompt)
            intobj["step"] += 1;
        await reaction.message.delete()


def extract_rank(msg):
    if isinstance(msg, str):
        rank = msg
    else:
        rank = msg.content.lower()
    if rank == "locked":
        rank = "lo"
    elif rank == "unranked":
        rank = "un"
    elif rank == "unrated":
        rank = "un"
    elif rank == "immortal":
        rank = "im"
    elif rank == "radiant":
        rank = "ra"
    else:
        rank = rank[0] + rank.split(" ")[1]
    return rank



client.run(os.environ["PF_TOKEN"])
