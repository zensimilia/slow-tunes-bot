from aiogram.contrib.fsm_storage.redis import AioRedisAdapterV2

PREFIX = "bot"


class RedisClient(AioRedisAdapterV2):
    """Wrapper for the redis client."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        prefix: str = PREFIX,
        **kwargs,
    ) -> None:
        super().__init__(host=host, port=port, prefix=prefix, **kwargs)

    def generate_key(self, *parts):
        """
        It takes a list of strings and joins them together with a colon in between each string

        @return A string
        """
        return ':'.join(self._prefix + tuple(map(str, parts)))
