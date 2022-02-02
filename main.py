import subprocess
from datetime import datetime
import math
import discord
import sqlite3
import os
from dotenv import load_dotenv
from discord.ext import commands
# from discord.ext.commands import client


intents=discord.Intents.all()


load_dotenv()
start_time = datetime.today()
client = commands.Bot(command_prefix='!', intents=intents)

con = sqlite3.connect('accounts.db')
cur = con.cursor()
# Create table
cur.execute("CREATE TABLE accounts (username CHAR(20), password CHAR(20), riotid CHAR(16), tag CHAR(5), rank INT, last_updated TIMESTAMP, added TIMESTAMP, PRIMARY KEY (username))")

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
async def add(ctx, *args):
    if len(args) == 0:
        await ctx.send("USAGE: `!add USERNAME PASSWORD RIOTID#TAG(optional) RANK(optional)`")
    elif len(args) == 2:
        cur.execute('INSERT INTO accounts VALUES ({},{},NULL ,NULL ,NULL, {},{})'.format(args[0], args[1], datetime.time()))
    elif len(args) == 3:
        cur.execute("INSERT")
    elif len(args) == 4:
        cur.execute("INSERT")
    else:
        await ctx.send("Too many arguments. USAGE: `!add USERNAME PASSWORD RIOTID#TAG(optional) RANK(optional)`")


client.run(os.environ["PF_TOKEN"])