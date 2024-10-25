from loguru import logger as log
import hikari

from embed import generate_embed
from database import Database

async def main():
    bot = hikari.GatewayBot(token="YOUR_BOT_TOKEN")

    db = Database()
    collection = db.get_collection("subscriptions")

    @bot.listen(hikari.StartedEvent)
    async def on_start(_):
        log.info("Bot started!")

        async for sub in collection.find({}):
            try:
                items = collection.find({'status': 'for_sale'})
                log.debug("{items} found for {id}", items=len(items), id=str(sub["_id"]))

                for item in items:
                    embed = generate_embed(item, sub["_id"], {'item': item})
                    await bot.rest.create_message(
                        sub["channel_id"],
                        embed=embed
                    )
            except Exception as e:
                log.error(f"Error processing subscription {sub['_id']}: {str(e)}")

    bot.run()

if __name__ == "__main__":
    main()
