import asyncio
import contextlib
import logging
import re
import subprocess
from functools import lru_cache
from typing import TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import AsyncIterator
    from pathlib import Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_sox_supported_formats() -> list[str]:
    try:
        output = subprocess.check_output(
            ["/usr/bin/sox", "--help"],
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="ignore",
        )
        match = re.search(r"AUDIO FILE FORMATS:\s*(.*)", output, re.IGNORECASE)
        if not match:
            return []
        return [fmt.lower() for fmt in match.group(1).strip().split()]
    except subprocess.CalledProcessError, FileNotFoundError:  # Исправлено
        return []


class AudioProcessorError(Exception): ...


class DownloadError(AudioProcessorError): ...


class ProcessError(AudioProcessorError): ...


class AudioProcessor:
    def __init__(self, command: list[str]) -> None:
        self.command = command
        self.__chunk_size = 64 * 1024

    async def process_file(self, file_path: str | Path) -> bytes: ...

    async def process_bytes(self, data: bytes) -> bytes: ...

    async def process_url(self, input_url: str) -> bytes:
        process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        bytes_iterator = self.__download_by_chunks(input_url)

        return await self.__execute(process, bytes_iterator)

    async def __download_by_chunks(self, url: str) -> AsyncIterator[bytes]:
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(self.__chunk_size):
                    yield chunk
        except aiohttp.ClientResponseError as err:
            raise DownloadError(f"Failed to download: {err.status}") from err

    async def __feed_process(self, process: Process, iterator: AsyncIterator[bytes]) -> None:
        if not process.stdin:
            return

        try:
            async for chunk in iterator:
                process.stdin.write(chunk)
                await process.stdin.drain()
        except BrokenPipeError, ConnectionResetError:
            logger.warning("AudioProcessor closed stdin prematurely")
        finally:
            if process.stdin.can_write_eof():
                process.stdin.write_eof()
            process.stdin.close()
            await process.stdin.wait_closed()

    async def __read_process(self, process: Process) -> bytes:
        if not process.stdout:
            raise RuntimeError

        return await process.stdout.read()

    async def __execute(self, process: Process, iterator: AsyncIterator[bytes]) -> bytes:
        try:
            _, processed_audio = asyncio.gather(
                self.__feed_process(process, iterator),
                self.__read_process(process),
                return_exceptions=True,
            )
            await process.wait()

            if process.returncode != 0 and process.stderr:
                raw_stderr = await process.stderr.read()
                msg_stderr = raw_stderr.decode().strip()
                raise ProcessError(f"AudioProcessor failed with code {process.returncode}: {msg_stderr}")

        except Exception:
            if process.returncode is None:
                with contextlib.suppress(BaseException):
                    process.kill()
            raise

        else:
            return processed_audio

    @property
    def formats(self) -> list[str]:
        return get_sox_supported_formats()

    def is_supported_format(self, fmt: str) -> bool:
        return fmt.lower().removeprefix(".") in self.formats
