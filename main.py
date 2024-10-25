from loguru import logger as log
import hikari
from database import Database
from embed import generate_embed
import asyncio

bot = hikari.GatewayBot(token="YOUR_BOT_TOKEN")

async def main():
    db = Database()
    collection = db.get_collection("subscriptions")

    @bot.listen(hikari.GuildMessageCreateEvent)
    async def on_message(event: hikari.GuildMessageCreateEvent):
        if event.message.content.lower() == "!check":
            await check_subscriptions(collection)

    async def check_subscriptions(collection):
        async for sub in collection.find({"status": "active"}):
            try:
                items = collection.find({"status": "active"})
                log.debug("{items} found for {id}", items=len(items), id=str(sub["_id"]))
                for item in items:
                    if str(item["user"]["feedback_count"]) != "0":
                        embed = generate_embed(item, sub["_id"], {"item": item})
                        await bot.rest.create_message(
                            channel=sub["channel_id"],
                            embed=embed
                        )
            except Exception as e:
                log.error(f"Error processing subscription {sub['_id']}: {str(e)}")
                continue

    bot.run()

if __name__ == "__main__":
    asyncio.run(main())
