import aiohttp
from typing import Literal, Union

from .constants import API_ROOT, VALID_LANGUAGES
from .models.auctions import (
    AuctionEntry,
    AuctionEntryExpanded,
    KubrowAuction,
    LichAuction,
    RivenAuction,
)
from .models.droptable import DropTable
from .models.enums import Element, Platform, Polarity
from .models.items import ItemFull, ItemShort
from .models.liches import LichEphemera, LichQuirk, LichWeapon
from .models.locations import Location
from .models.missions import NPC, PartialMission
from .models.orders import OrderRow
from .models.rivens import RivenAttribute, RivenItem
from .models.users import CurrentUser
from .utils import _from_data, _raise_error_code, format_name


class PyTennoBackend:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def _request(self, url: str, **kwargs) -> dict[str, str | int | dict | list]:
        url = f"{API_ROOT}{url}"
        mode = getattr(self._session, kwargs.pop("method", "get"))

        response: aiohttp.ClientResponse = await mode(url, **kwargs)
        if response.status != 200:
            _raise_error_code(response.status)
        return await response.json()


class AuthBackend(PyTennoBackend):
    async def _login(
        self,
        email: str,
        password: str,
    ):
        url = "/auth/signin"
        data = {
            "auth_type": "header",
            "email": email,
            "password": password,
        }
        response = await self._request(url, json=data, method="post")
        return _from_data(CurrentUser, response["payload"]["user"])


class ItemBackend(PyTennoBackend):
    async def _get_items(self, language: str):
        url = "/items"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)

        return [_from_data(ItemShort, node) for node in response["payload"]["items"]]

    async def _get_item(
        self,
        item_name: str,
        platform: str,
    ):
        url = f"/items/{format_name(item_name)}"
        headers = {"Platform": platform}
        response = await self._request(url, headers=headers)
        items = response["payload"]["item"]["items_in_set"]

        return [_from_data(ItemFull, node) for node in items]

    async def _get_orders(
        self,
        item_name,
        include_items,
        platform,
    ):
        url = f"/items/{format_name(item_name)}/orders"
        headers = {"Platform": platform}

        if include_items:
            url += "?include=item"

        response = await self._request(url, headers=headers)
        if include_items:
            return (
                [_from_data(OrderRow, node) for node in response["payload"]["orders"]],
                [
                    _from_data(ItemFull, node)
                    for node in response["include"]["item"]["items_in_set"]
                ],
            )
        return [_from_data(OrderRow, node) for node in response["payload"]["orders"]]

    async def _get_droptable(
        self, item_name, include_items: bool, language: VALID_LANGUAGES
    ):
        url = f"/items/{format_name(item_name)}/droptables"
        if include_items:
            url += "?include=item"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        if include_items:
            return (
                DropTable._from_data(response["droptables"]),
                [
                    ItemFull._from_data(item)
                    for item in response["include"]["item"]["items_in_set"]
                ],
            )
        return _from_data(DropTable, response["droptables"])


class LichBackend(PyTennoBackend):
    async def _get_weapons(self, language):
        url = "/lich/weapons"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [_from_data(LichWeapon, node) for node in response["payload"]["weapons"]]

    async def _get_ephemeras(self, language):
        url = "/lich/ephemeras"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [
            _from_data(LichEphemera, node) for node in response["payload"]["ephemeras"]
        ]

    async def _get_quirks(self, language):
        url = "/lich/quirks"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [_from_data(LichQuirk, node) for node in response["payload"]["quirks"]]


class RivenBackend(PyTennoBackend):
    async def _get_riven_items(self, language):
        url = "/riven/items"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [_from_data(RivenItem, node) for node in response["payload"]["items"]]

    async def _get_riven_attributes(self, language):
        url = "/riven/attributes"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [
            _from_data(RivenAttribute, node)
            for node in response["payload"]["attributes"]
        ]


class MiscBackend(PyTennoBackend):
    async def _get_locations(self, language):
        url = "/misc/locations"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [_from_data(Location, node) for node in response["payload"]["locations"]]

    async def _get_npcs(self, language):
        url = "/misc/npc"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [_from_data(NPC, node) for node in response["payload"]["npc"]]

    async def _get_missions(self, language):
        url = "/misc/missions"
        headers = {"Language": language}
        response = await self._request(url, headers=headers)
        return [
            _from_data(PartialMission, node) for node in response["payload"]["missions"]
        ]


class AuctionsBackend(PyTennoBackend):
    async def _create_auction(
        self,
        item: Union[RivenAuction, LichAuction, KubrowAuction],
        note: str,
        starting_price: int,
        buyout_price: int,
        minimal_reputation: int = 0,
        minimal_increment: int = 1,
        private: bool = False,
    ):
        url = "/auctions/create"
        attributes = [
            {
                [
                    {
                        "positive": attribute.positive,
                        "value": attribute.value,
                        "url": attribute.url_name,
                    }
                ]
                for attribute in item.attributes
            }
        ]
        data = {
            "note": note,
            "starting_price": starting_price,
            "buyout_price": buyout_price,
            "minimal_reputation": minimal_reputation,
            "minimal_increment": minimal_increment,
            "private": private,
            "item": {
                "type": item.type.name.lower(),
                "attributes": attributes,
                "name": item.name.lower(),
                "mastery_level": item.mastery_level,
                "re_rolls": item.re_rolls,
                "weapon_url_name": item.weapon_url_name,
                "polarity": item.polarity.name.lower(),
                "mod_rank": item.mod_rank,
            },
        }

        response = await self._request(url, method="post", data=str(data))
        return _from_data(AuctionEntry, response["payload"]["auction"])

    async def _find_riven_auctions(
        self,
        *,
        platform: Platform,
        buyout_policy: Literal["with", "direct", "all"] = "all",
        weapon_url_name: str,
        mastery_rank_min: int,
        mastery_rank_max: int,
        re_rolls_min: int = 0,
        re_rolls_max: int = None,
        positive_stats: str,
        negative_stats: str = None,
        polarity: Polarity = Polarity.any,
        mod_rank: Literal["any", "maxed"] = "any",
        sort_by: Literal[
            "price_desc", "price_asc", "positive_attr_desc", "positive_attr_asc"
        ] = "price_desc",
        operation: Literal["anyOf", "allOf"] = "allOf",
    ):
        url = f"/auctions/search?type=riven&"
        +f"weapon_url_name={weapon_url_name}&"
        +f"mastery_rank_min={mastery_rank_min}&"
        +f"mastery_rank_max={mastery_rank_max}&"
        +f"re_rolls_min={re_rolls_min}&"
        +f"re_rolls_max={re_rolls_max}&"
        +f"positive_stats={positive_stats}&"
        +f"negative_stats={negative_stats}&"
        +f"polarity={polarity.name.lower()}&"
        +f"mod_rank={mod_rank}&"
        +f"sort_by={sort_by}&"
        +f"operation={operation}&"
        +f"buyout_policy={buyout_policy}"
        # pain
        headers = {"Platform": platform.name.lower()}
        response = await self._request(url, headers=headers)

        return [
            _from_data(AuctionEntryExpanded, node)
            for node in response["payload"]["auctions"]
        ]

    async def _find_lich_auctions(
        self,
        *,
        platform: Platform,
        weapon_url_name: str,
        element: Element,
        ephemera: bool,
        damage_min: int,
        damage_max: int,
        quirk_url_name: str,
        sort_by: Literal[
            "price_desc", "price_asc", "positive_attr_desc", "positive_attr_asc"
        ] = "price_desc",
        buyout_policy: Literal["with", "direct", "all"] = "all",
    ):
        url = f"/auctions/search?type=lich&"
        +f"weapon_url_name={weapon_url_name}&"
        +f"element={element.name.lower()}&"
        +f"ephemera={ephemera}&"
        +f"damage_min={damage_min}&"
        +f"damage_max={damage_max}&"
        +f"quirk={quirk_url_name}&"
        +f"sort_by={sort_by}&"
        +f"buyout_policy={buyout_policy}"
        headers = {"Platform": platform.name.lower()}
