import asyncio
import os
import json
import hikari
import lightbulb
from loguru import logger as log
from api import search_item
from database import Database
from scraper import generate_embed, scrape

def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)

config = load_config()
bot = lightbulb.BotApp(token=config["discord_token"])
db = Database.get_instance()

async def run_background() -> None:
    log.info("Scraper started.")
    while True:
        log.info("Executing scraping loop")
        for sub in db.get_subscriptions():
            items = scrape(db, sub)
            if items:
                log.debug("{items} found for {id}", items=len(items), id=str(sub["_id"]))
                for item in items:
                    item_res = search_item(item["id"])
                    if item_res:
                        if str(item_res["item"]["user"]["feedback_count"]) != "0":
                            embed = generate_embed(item, sub["_id"], item_res)
                            await bot.rest.create_message(sub["channel_id"], embed=embed)

            if len(items) > 0:
                # Update last_sync timestamp for the subscription
                db.update_last_sync(sub["_id"], int(items[0]["photo"]["high_resolution"]["timestamp"]))

        log.info("Sleeping for {interval} seconds", interval=60)
        await asyncio.sleep(int(60))

@bot.listen(hikari.ShardReadyEvent)
async def ready_listener(_):
    log.info("Bot is ready")
    log.info("{count} subscriptions registered", count=len(db.get_subscriptions()))
    asyncio.create_task(run_background())

@bot.command()
@lightbulb.option("url", "URL to vinted search", type=str, required=True)
@lightbulb.option("channel_name", "Name of the channel for alerts", type=str, required=True)
@lightbulb.option("category_id", "ID of category for alerts", type=str, required=True)
@lightbulb.command("subscribe", "Subscribe to a Vinted search")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscribe(ctx: lightbulb.Context) -> None:
    guild_id = ctx.interaction.guild_id

    if guild_id:
        guild = bot.cache.get_guild(int(guild_id))

        if guild:
            category_id = ctx.options.category_id

            if category_id:
                alert_category = guild.get_channel(int(category_id))

                if alert_category and isinstance(alert_category, hikari.GuildCategory):
                    new_channel = await guild.create_text_channel(ctx.options.channel_name, category=alert_category)
                    subscription_id = db.insert_subscription(ctx.options.url, new_channel.id)
                    log.info("Subscription created for {url}", url=ctx.options.url)
                    await ctx.respond(f"? Created subscription in #{new_channel.name} under {alert_category.name}")
                else:
                    await ctx.respond("? Error: Could not find the specified category by ID.")
            else:
                await ctx.respond("? Error: CATEGORY_ID is not defined in the environment variables.")
        else:
            await ctx.respond("? Error: Could not find the server (guild). Please use this command in a server (guild).")
    else:
        await ctx.respond("? Error: Could not obtain the server (guild) ID.")

@bot.command()
@lightbulb.command("subscriptions", "Get a list of subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def subscriptions(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title="Subscriptions")

    for sub in db.get_subscriptions():
        embed.add_field(name="#" + str(sub["_id"]), value=sub["url"])

    await ctx.respond(embed)

@bot.command()
@lightbulb.option("id", "ID of the subscription", type=int, required=True)
@lightbulb.command("unsubscribe", "Stop following a subscription")
@lightbulb.implements(lightbulb.SlashCommand)
async def unsubscribe(ctx: lightbulb.Context) -> None:
    subscription_id = ctx.options.id
    result = db.delete_subscription(subscription_id)

    if result.deleted_count > 0:
        # Obtain the channel object from the channel ID in the subscription
        channel = bot.cache.get_guild(ctx.interaction.guild_id).get_channel(subscription["channel_id"])

        if channel:
            # Delete the channel
            await channel.delete()
            log.info("Deleted subscription #{id}", id=str(subscription_id))
            await ctx.respond(f"?? Deleted subscription #{str(subscription_id)}.")
        else:
            await ctx.respond("? Error: Could not find the channel to delete.")
    else:
        await ctx.respond("? Error: Subscription not found with ID {id}.", id=str(subscription_id))

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()

    bot.run(
        activity=hikari.Activity(
            name="Vinted!", type=hikari.ActivityType.WATCHING
        )
    )
