from typing import Any, Dict, List
from database import Database
import discord
from lightbulb import BotApp
from datetime import datetime

from api import search
from loguru import logger as log


def scrape(db: Database, params: Dict[str, Any]) -> List:
    """
    Scrape items and filter by new results

    Args:
        params (Dict[str, Any]): Subscription parameters

    Returns:
        List: list of new items
    """
    response = search(params["url"], {"per_page": 20})

    # Remove promoted items
    try:
        items = [item for item in response["items"] if item["promoted"] == False]
    except KeyError:
        return []

    # Skip null
    if not len(items):
        return []

    # Ignore items for first sync
    if params["last_sync"] == -1:
        return [items[0]]

    # Filter date and by existing
    results = []
    for item in items:
        try:
            timestamp = item["photo"]["high_resolution"]["timestamp"]
        except Exception:
            log.warning(f"Empty timestamp found for item {item.get('id', 'unknown')}")
            print(item)
            continue

        if timestamp > params["last_sync"] and "id" in item:
            if not db.item_exists(str(item["id"]), str(params["channel_id"])):
                results.append(item)
                try:
                    db.insert_item(item, str(params["channel_id"]))
                except ValueError as e:
                    log.error(f"Failed to insert item: {e}")
                    continue

    return results


def generate_embed(item: Any, sub_id: int, item_res: Any) -> discord.Embed:
    """
    Generate an embed with item details

    Args:
        item (Any): Scraped item
        sub_id (int): Subscription ID

    Returns:
        discord.Embed: Generated embed
    """
    if str(item["currency"]) == "EUR":
        currency = "?"
    else:
        currency = " " + str(item["currency"])
    embed = discord.Embed()
    embed.title = item["title"]
    embed.url = item["url"]
    embed.set_image(item["photo"]["url"])
    embed.color = 0x09B1BA
    embed.add_field(name="? Prix", value="```" + str(item["price"]) + currency + " | " + str(item_res["item"]["total_item_price"]) + currency + " TTC ```", inline=True)
    embed.add_field(name="? Etat", value="```" + item_res["item"]["status"] + "```", inline=True)
    embed.add_field(name="? Avis", value="```?" + str(item_res["item"]["user"]["positive_feedback_count"]) + " - ?" + str(item_res["item"]["user"]["negative_feedback_count"]) + "```", inline=True)
    embed.add_field(name=":label: Marque", value="```" + item_res["item"]["brand"] + "```", inline=True)
    embed.add_field(name="? Taille", value="```" + item["size_title"] + "```", inline=True)
    embed.add_field(name="? Loc", value="```" + item_res["item"]["user"]["city"] + " (" + item_res["item"]["user"]["country_title"] + ")" + "```", inline=True)
    date = datetime.fromtimestamp(
        int(item["photo"]["high_resolution"]["timestamp"])
    ).strftime("%d/%m/%Y, %H:%M:%S")
    embed.set_footer(text=f'Published on {date} ? Subscription #{str(sub_id)}')
    embed.set_author(
        name="Posted by " + item["user"]["login"],
        url=item["user"]["profile_url"],
    )

    return embed
