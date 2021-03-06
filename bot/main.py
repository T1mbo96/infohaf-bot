import discord
from discord.ext import commands
import os
import sqlalchemy as db


client = commands.Bot(command_prefix=".")
ENGINE = db.create_engine(os.getenv("DATABASE_URL"))
connection = ENGINE.connect()
META_DATA = db.MetaData(bind=connection)
META_DATA.reflect()
challenges = META_DATA.tables['Challenges']


TOKEN = os.getenv("DISCORD_BOT_TOKEN")
USERS = ["T1mbo96#1861", "NPC#0770"]
EVENTCHANNEL = 780013047761600533


def get_current_active():
    """
    Access Database and search for challenges.
    :return: False if no challenge is active, str (flag) else
    """
    statement = (
        db.select([challenges]).
        where(challenges.c.status)
    )
    results = connection.execute(statement).fetchall()
    if not results:
        return False
    else:
        return results[-1][-2]


def add_challenge(flag, challenge):
    statement = db.select([challenges])
    id_ = len(connection.execute(statement).fetchall()) + 1
    statement = db.insert(challenges).values(id=id_, exercise=challenge, flag=flag, status=True)
    connection.execute(statement)


def end_challenge():
    if not get_current_active():
        return False
    else:
        statement = (
            db.update(challenges).
            where(challenges.c.status).
            values(status=False)
        )
        connection.execute(statement)
        return True


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game("Wartet auf Flaggen: .flag ctf{example123}"))
    print("I am online")


@client.command(name="info")
async def info(ctx):
    """
    Return latency and flag of the current challenge (if active).
    """
    await ctx.send(f"Latenz: {str(round(client.latency, 2))}")
    if str(ctx.author) in USERS:
        flag = get_current_active()
        if flag is False:
            await ctx.send("Keine aktive Challenge")
        else:
            await ctx.send(f"Aktive Challenge, Flag: {flag}")


@client.command(name="startEvent")
async def startEvent(ctx):
    """
    Start a new challenge.
    Use Markdown for the formation of the text.
    Usage: .startEvent #example text#ctf{example123}
    """
    header, challenge, flag = ctx.message.content.split("#")

    channel = ctx.message.channel
    if not ("Direct Message" in str(channel)):
        await ctx.message.delete()

    if flag == "" or challenge == "":
        await ctx.send("Bitte Flagge und Challenge anhängen: .startEvent Aufgabe ctf{example123}")
    elif str(ctx.author) not in USERS:
        await ctx.send("Du hast nicht die Berechtigung diese Aktion durchzuführen!")

    elif get_current_active() is not False:
        await ctx.send("Es läuft bereits eine Challenge! Nutze .endEvent um dieses zu beenden.")
    else:
        add_challenge(flag, challenge.encode())
        await ctx.send("Challenge gestartet!")
        channel = client.get_channel(EVENTCHANNEL)
        await channel.send(challenge)


@client.command(name="endEvent")
async def endEvent(ctx):
    """
    Stop the current challenge.
    """
    if str(ctx.author) not in USERS:
        await ctx.send("Du hast nicht die Berechtigung diese Aktion durchzuführen!")
    else:
        if end_challenge():
            await ctx.send("Challenge beendet!")
        else:
            await ctx.send("Es gibt keine aktive Challenge!")


@client.command(name="flag")
async def flag(ctx, flag):
    """
    Evaluate flag. Usage: .flag example{123}
    """
    channel = ctx.message.channel
    if not ("Direct Message" in str(channel)):
        await ctx.message.delete()
        start = f"@{str(ctx.message.author).split('#')[0]} : "
    else:
        start = ""

    flag_ = get_current_active()
    if flag_ is False:
        await ctx.send("Keine aktive Challenge")
    elif flag == flag_:
        await ctx.send(start + "Richtig! Du hast es geschaft! :)")
    else:
        await ctx.send(start + "Leider falsch! Versuch es einfach erneut :(")


if __name__ == '__main__':
    client.run(TOKEN)