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


def generate_embed(item: Any, sub_id: int, item_res: Any) -> hikari.Embed:
    """
    Generate an embed with item details
    """
    try:
        # Create base embed
        embed = hikari.Embed(
            title=item.get("title", "No Title"),
            url=item.get("url", ""),
            color=hikari.Color(0x09B1BA)
        )

        # Set image if available
        if item.get("photo", {}).get("url"):
            embed.set_image(item["photo"]["url"])

        # Add price information
        currency = "?" if item.get("currency") == "EUR" else f" {item.get('currency', '')}"
        price = f"{item.get('price', 'N/A')}{currency}"
        total_price = f"{item_res.get('item', {}).get('total_item_price', 'N/A')}{currency}"
        embed.add_field("Price", f"```{price} | {total_price} Total```", inline=True)

        # Add item details
        embed.add_field("Condition", f"```{item_res.get('item', {}).get('status', 'N/A')}```", inline=True)
        embed.add_field("Brand", f"```{item_res.get('item', {}).get('brand', 'N/A')}```", inline=True)
        embed.add_field("Size", f"```{item.get('size_title', 'N/A')}```", inline=True)

        # Add user information
        user_data = item_res.get('item', {}).get('user', {})
        location = f"{user_data.get('city', 'N/A')} ({user_data.get('country_title', 'N/A')})"
        embed.add_field("Location", f"```{location}```", inline=True)

        # Set footer with timestamp
        if item.get("photo", {}).get("high_resolution", {}).get("timestamp"):
            date = datetime.fromtimestamp(int(item["photo"]["high_resolution"]["timestamp"]))
            embed.set_footer(f'Published on {date.strftime("%d/%m/%Y, %H:%M:%S")} ? Subscription #{str(sub_id)}')

        # Set author
        if item.get("user", {}).get("login"):
            embed.set_author(
                name=f"Posted by {item['user']['login']}",
                url=item['user'].get('profile_url', '')
            )

        return embed
    except Exception as e:
        log.error(f"Error generating embed: {e}")
        return hikari.Embed(title="Error", description="Failed to generate item embed")
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
