import argparse
import asyncio
import os
import socket
import time
import logging

import uvloop

from pymcached import commands
from pymcached.models import Data

uvloop.install()


stream_handler = logging.StreamHandler()
logging.basicConfig(
    handlers=[stream_handler],
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# COMMANDS: set, add, replace. get.:q
#


_data_storage: dict[str, Data] = {}
_start_time = int(time.time())
_pid = os.getpid()


async def handle_memcached_client(reader, writer):
    expecting_payload = 0
    buffer = bytearray()
    noreply = False
    command_parts = []
    quitted = False

    logger.debug('Received connection from %s', writer.get_extra_info('peername'))

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
                elif command_parts[0] == "stats":
                    response = ""
                    response += f"pid {_pid}\r\n"
                    response += f"uptime {int(time.time()-_start_time)}\r\n"
                    response += f"time {int(time.time())}\r\n"
                    response += "END\r\n"
                    writer.write(response.encode())
                    await writer.drain()
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


async def main(address: str, port: int):
    server = await asyncio.start_server(handle_memcached_client, address, port)
    async with server:
        logger.info(f'Listening on {address}:{port}')
        await server.serve_forever()

    await server.wait_closed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port", help="Port to listen on", type=int, default=11211
    )
    parser.add_argument(
        "-l", "--address", help="Address to listen on", default="127.0.0.1"
    )
    parser.add_argument(
        "-v", "--verbose", help="Show verbose messages", action="store_true"
    )

    arguments = parser.parse_args()

    if arguments.verbose:
        logger.setLevel(logging.DEBUG)

    if arguments.port < 1 or arguments.port > 65535:
        msg = "Port must be in range 1-65535"
        raise ValueError(msg)

    network_addresses = [
        i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)
    ]
    network_addresses.append("127.0.0.1")

    if arguments.address not in network_addresses:
        msg = "Address must be one of {}"
        raise ValueError(msg.format(",".join(network_addresses)))

    asyncio.run(main(arguments.address, arguments.port))
