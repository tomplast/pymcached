import asyncio

import uvloop

from pymcached import commands
from pymcached.models import Data

uvloop.install()


# COMMANDS: set, add, replace. get.:q
#


_data_storage: dict[str, Data] = {}


async def handle_memcached_client(reader, writer):
    expecting_payload = 0
    buffer = bytearray()
    noreply = False
    command_parts = []
    quitted = False

    while True and not quitted:
        data = await reader.read(1024)
        if not data:
            break

        buffer += data

        while b"\r\n" in buffer:
            command_end = buffer.index(b"\r\n")

            if not expecting_payload:
                command_parts = buffer[:command_end].decode("utf-8").split(" ")

                noreply = command_parts[-1] == "noreply"

                if command_parts[0] in ["set", "add", "replace"]:
                    expecting_payload = True
                elif command_parts[0] == "quit":
                    quitted = True
                    break

                else:
                    response = "ERROR\r\n"
                    response = getattr(commands, f"run_{command_parts[0]}")(
                        _data_storage, command_parts
                    )
                    writer.write(response)
                    await writer.drain()

            else:
                expecting_payload = False

                response = "ERROR\r\n"
                response = getattr(commands, f"run_{command_parts[0]}")(
                    _data_storage, command_parts, buffer[:command_end].decode()
                )

                if not noreply and not expecting_payload:
                    writer.write(response)
                    await writer.drain()

            del buffer[: command_end + 2]
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_memcached_client, "127.0.0.1", 11211)
    async with server:
        await server.serve_forever()

    await server.wait_closed()


asyncio.run(main())
