from typing import Any, Dict, List
from database import Database
import hikari
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
            log.warning("Empty timestamp found")
            print(item)
            continue

        if timestamp > params["last_sync"] and "id" in item:
            if not db.item_exists(item["id"], params["channel_id"]):
                results.append(item)
                db.insert_item(item["id"], params["channel_id"])

    return results


def generate_embed(item: Any, sub_id: int, item_res: Any) -> hikari.Embed:
    """
    Generate an embed with item details

    Args:
        item (Any): Scraped item
        sub_id (int): Subscription ID

    Returns:
        hikari.Embed: Generated embed
    """
    if str(item["currency"]) == "EUR":
        currency = "?"
    else:
        currency = " " + str(item["currency"])
    embed = hikari.Embed()
    embed.title = item["title"]
    embed.url = item["url"]
    embed.set_image(item["photo"]["url"])
    embed.color = hikari.Color(0x09B1BA)
    embed.add_field("? Prix", "```" + str(item["price"]) + currency + " | " + str(item_res["item"]["total_item_price"]) + currency + " TTC ```", inline=True)
    embed.add_field("? Etat", "```" + item_res["item"]["status"] + "```", inline=True)
    embed.add_field("? Avis", "```?" + str(item_res["item"]["user"]["positive_feedback_count"]) + " - ?" + str(item_res["item"]["user"]["negative_feedback_count"]) + "```", inline=True)
    embed.add_field(":label: Marque", "```" + item_res["item"]["brand"] + "```", inline=True)
    embed.add_field("? Taille", "```" + item["size_title"] + "```", inline=True)
    embed.add_field("? Loc", "```" + item_res["item"]["user"]["city"] + " (" + item_res["item"]["user"]["country_title"] + ")" + "```", inline=True)
    
    date = datetime.fromtimestamp(
        int(item["photo"]["high_resolution"]["timestamp"])
    ).strftime("%d/%m/%Y, %H:%M:%S")
    embed.set_footer(f'Published on {date} ? Subscription #{str(sub_id)}')
    embed.set_author(
        name="Posted by " + item["user"]["login"],
        url=item["user"]["profile_url"],
    )

    return embed
