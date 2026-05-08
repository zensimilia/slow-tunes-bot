import asyncio
import logging
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import aiofiles
import aiohttp

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import AsyncIterator
    from pathlib import Path

T = TypeVar("T")

CHUNK_SIZE = 64 * 1024  # 64 kb
PROCESS_TIMEOUT = 60 * 3  # 3 min
KILL_TIMEOUT = 5  # 5 sec

logger = logging.getLogger(__name__)


class AudioProcessorError(Exception): ...


class DownloadError(AudioProcessorError): ...


class ProcessError(AudioProcessorError): ...


class ProcessorBuilderProtocol[T](Protocol):
    def __str__(self) -> str: ...
    def build(self) -> list[str]: ...
    def speed(self, *args: Any, **kwargs: Any) -> T: ...
    def reverb(self, *args: Any, **kwargs: Any) -> T: ...


class AudioProcessor[T]:
    def __init__(self, command_builder: ProcessorBuilderProtocol[T]) -> None:
        self.command_builder = command_builder
        self.chunk_size: int = CHUNK_SIZE
        self.process_timeout: float = PROCESS_TIMEOUT

    async def _create_process(self) -> Process:
        logger.debug("Start process command: %s", self.command_builder)
        return await asyncio.create_subprocess_exec(
            *self.command_builder.build(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def process(
        self,
        data: AsyncIterator[bytes],
    ) -> bytes:
        process = await self._create_process()
        return await self._execute(process, data)

    async def process_file(self, file_path: str | Path) -> bytes:
        return await self.process(self._read_by_chunks(file_path, self.chunk_size))

    async def process_bytes(self, data: bytes) -> bytes:
        return await self.process(self._cut_by_chunks(data, self.chunk_size))

    async def process_url(
        self,
        url: str,
        *,
        method: str = "GET",
        session: aiohttp.ClientSession,
        **request_kwargs: Any,
    ) -> bytes:
        return await self.process(self._download_by_chunks(url, method=method, session=session, **request_kwargs))

    async def _download_by_chunks(
        self,
        url: str,
        *,
        method: str,
        session: aiohttp.ClientSession,
        **request_kwargs: Any,
    ) -> AsyncIterator[bytes]:
        try:
            async with session.request(method, url, **request_kwargs) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(self.chunk_size):
                    yield chunk
        except aiohttp.ClientError as err:
            raise DownloadError(err) from err

    async def _cut_by_chunks(self, data: bytes, chunk_size: int) -> AsyncIterator[bytes]:
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def _read_by_chunks(self, file_path: str | Path, chunk_size: int) -> AsyncIterator[bytes]:
        async with aiofiles.open(file_path, mode="rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    async def _feed_process(self, process: Process, data: AsyncIterator[bytes]) -> None:
        if not process.stdin:
            raise RuntimeError("Process stdin is not available")

        try:
            async for chunk in data:
                process.stdin.write(chunk)
                await process.stdin.drain()
        except BrokenPipeError, ConnectionResetError:
            logger.warning("AudioProcessor closed stdin prematurely")
        finally:
            if process.stdin.can_write_eof():
                process.stdin.write_eof()
            process.stdin.close()
            await process.stdin.wait_closed()

    async def _run_tasks(self, process: Process, data: AsyncIterator[bytes]) -> tuple[bytes, bytes]:
        if not process.stdout or not process.stderr:
            raise RuntimeError("Process stdout/stderr is not available")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._feed_process(process, data))
            stdout = tg.create_task(process.stdout.read())
            stderr = tg.create_task(process.stderr.read())

        return stdout.result(), stderr.result()

    async def _stop_process(self, process: Process, *, kill: bool = False) -> None:
        if process.returncode is not None:
            return
        if kill:
            process.kill()
        else:
            process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=KILL_TIMEOUT)
        except TimeoutError:
            process.kill()
            await process.wait()

    async def _execute(self, process: Process, data: AsyncIterator[bytes]) -> bytes:
        returncode: int

        try:
            stdout, stderr = await asyncio.wait_for(self._run_tasks(process, data), timeout=self.process_timeout)
            stderr = stderr.decode(errors="replace").strip()
            logger.debug("Process stderr:\n%s", stderr)
            returncode = await asyncio.wait_for(process.wait(), timeout=KILL_TIMEOUT)
        except* TimeoutError as eg:
            await self._stop_process(process, kill=True)
            raise ProcessError("Processing timeout") from eg
        except* asyncio.CancelledError:
            await self._stop_process(process, kill=True)
            raise
        except* Exception as eg:
            await self._stop_process(process, kill=True)
            raise ProcessError(eg.exceptions) from eg

        if returncode != 0:
            raise ProcessError(f"Process failed ({returncode}): {stderr}")

        return stdout
