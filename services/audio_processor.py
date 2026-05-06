import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Protocol

import aiohttp

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import AsyncIterator
    from pathlib import Path

logger = logging.getLogger(__name__)


class AudioProcessorError(Exception): ...


class DownloadError(AudioProcessorError): ...


class ProcessError(AudioProcessorError): ...


class UnsupportedFormatError(AudioProcessorError):
    def __init__(self, fmt: str) -> None:
        super().__init__(f"Format {fmt} is unsupported")


class ProcessorBuilderProtocol(Protocol):
    def __str__(self) -> str: ...
    def build_list(self) -> list[str]: ...
    def build_string(self) -> str: ...
    def get_suported_formats(self) -> list[str]: ...
    def is_format_supported(self, fmt: str) -> bool: ...
    def get_format(self) -> str: ...


class AudioProcessor:
    def __init__(self, command_builder: ProcessorBuilderProtocol) -> None:
        self.command_builder = command_builder
        self.__chunk_size = 64 * 1024
        self.__process_timeout = 30

    async def process_file(self, file_path: str | Path) -> bytes: ...  # TODO @me: implement

    async def process_bytes(self, data: bytes) -> bytes: ...  # TODO @me: implement

    async def process_url(self, input_url: str) -> bytes:
        process = await asyncio.create_subprocess_exec(
            *self.command_builder.build_list(),
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
            raise DownloadError(err.message) from err

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
        fmt = self.command_builder.get_format()
        if not self.is_supported_format(fmt):
            process.terminate()
            raise UnsupportedFormatError(fmt)
        tasks = [self.__feed_process(process, iterator), self.__read_process(process)]
        try:
            _, processed_audio = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self.__process_timeout,
            )
            await process.wait()

        except Exception as err:
            logger.exception("Error while processing")
            if process.returncode is None:
                with contextlib.suppress(BaseException):
                    process.kill()
                    await process.wait()
            raise ProcessError(err) from err

        if process.returncode != 0 and process.stderr:
            raw_stderr = await process.stderr.read()
            msg_stderr = raw_stderr.decode().strip()
            msg_raise = f"AudioProcessor failed with code {process.returncode}: {msg_stderr}"
            raise ProcessError(msg_raise)

        return processed_audio

    @property
    def formats(self) -> list[str]:
        return self.command_builder.get_suported_formats()

    def is_supported_format(self, fmt: str) -> bool:
        return self.command_builder.is_format_supported(fmt)
