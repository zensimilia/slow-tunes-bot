from typing import TYPE_CHECKING

from aiogram.filters import BaseFilter

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message


class IsAdmin(BaseFilter):
    """
    Filter to check if the user is in the list of administrators.

    This filter compares the ID of the user who sent the message or
    triggered the callback with a predefined list of admin IDs.
    """

    def __init__(self, admin_ids: list[int] | None = None) -> None:
        """
        Initialize the filter with a list of allowed IDs.

        Args:
            admin_ids (optional): A list of user IDs that should have admin access.

        Notes:
            If `admin_ids` is None then filter always return True.
        """
        self._admin_ids = admin_ids

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        """
        Check if the event's user ID is in the admin list.

        Args:
            obj: The incoming Telegram event (Message or CallbackQuery).

        Returns:
            True if the user is an admin, False otherwise.
        """
        if self._admin_ids is None:
            return True

        if obj.from_user:
            return obj.from_user.id in self._admin_ids
        return False
