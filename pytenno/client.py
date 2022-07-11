from types import TracebackType
from typing import Optional, Type

import aiohttp

from ._backends.core import PyTennoBackend
from .constants import VALID_LANGUAGES
from .interface.auction_entries import AuctionEntries
from .interface.auctions import Auctions
from .interface.auth import Auth
from .interface.items import Items
from .interface.liches import Liches
from .interface.misc import Misc
from .interface.profile import Profile
from .interface.rivens import Rivens
from .models.enums import Platform


class PyTenno:
    """The primary class for interaction with the warframe.market API endpoints.
    This must be used in an asynchronous context manager.

    Parameters
    ----------

    default_language : str
        The default language used when communicating with the API.
        See ``VALID_LANGUAGES`` for valid values.
    default_platform : Platform
        The default platform used when communicating with the API.
    silenced_errors  : list[Exception]
        A list of errors that will be silenced when raised by the API.
        Instead of raising the error, the function will return None.

    Returns
    -------
    PyTenno

    Example
    -------
    >>> async with PyTenno() as tenno:
    >>>     current_user = await tenno.Auth.login(username="username", password="password")
    >>>     print(current_user.ingame_name)
    """

    def __init__(
        self, *,
        default_language: Optional[VALID_LANGUAGES] = "en",
        default_platform: Platform = Platform.pc,
        silenced_errors: list[Exception] = [],
    ) -> None:
        self._language = default_language
        self._platform = default_platform

        self._session: aiohttp.ClientSession
        self._silenced = silenced_errors

        self.AuctionEntries: AuctionEntries
        self.Auctions: Auctions
        self.Auth: Auth
        self.Items: Items
        self.Liches: Liches
        self.Misc: Misc
        self.Profile: Profile
        self.Rivens: Rivens

    async def __aenter__(self):
        headers = {
            "Authorization": "JWT",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "language": self._language,
            "platform": self._platform.name,
        }
        self._session = aiohttp.ClientSession(headers=headers)
        backend = PyTennoBackend(self._session, self._silenced)

        self.AuctionEntries = AuctionEntries(backend)
        self.Auctions = Auctions(backend)
        self.Auth = Auth(backend)
        self.Items = Items(backend)
        self.Liches = Liches(backend)
        self.Misc = Misc(backend)
        self.Profile = Profile(backend)
        self.Rivens = Rivens(backend)
        return self

    async def __aexit__(
        self,
        exctype: Optional[Type[BaseException]],
        excinst: Optional[BaseException],
        exctb: Optional[TracebackType],
    ) -> bool:
        await self._session.close()
        return False
    
    async def close(self) -> None:
        """Closes the session."""
        await self._session.close()