import aiohttp
from pytenno.interface.extensions import AuctionEntries, Auctions, Auth, Items, Liches, Misc, Rivens
from pytenno.models.enums import Platform
from types import TracebackType
from typing import Optional, Type

from ._backends import PyTennoBackend

from ..constants import VALID_LANGUAGES


class PyTenno:
    """The primary class for interaction with the warframe.market API endpoints."""
    def __init__(
        self,
        language: VALID_LANGUAGES = "en",
        platform: Platform = Platform.pc,
        silenced_errors: list[Exception] = [],
    ) -> None:
        """Initialize the PyTenno client. This must be used in an asynchronous context manager.

        Parameters:
        
        - `language`: :class:`VALID_LANGUAGES`
            The default language used when communicating with the API.
        - `platform`: :class:`Platform`
            The default platform used when communicating with the API.
        - `silenced_errors`: list[:class:`BaseError`]
            A list of errors that will be silenced when raised by the API.
            Instead of raising the error, the function will return None.
        
        Returns
        --------
        - :class:`PyTenno`

        Examples:
        ---------
        >>> async with PyTenno() as tenno:
        >>>     current_user = await tenno.Auth.login(username="username", password="password")
        >>>     print(current_user.ingame_name)
        """
        self._language = language
        self._platform = platform

        self._session: aiohttp.ClientSession = None
        self._silenced = silenced_errors

        self.AuctionEntries: AuctionEntries
        self.Auctions: Auctions
        self.Auth: Auth
        self.Items: Items
        self.Liches: Liches
        self.Misc: Misc
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
