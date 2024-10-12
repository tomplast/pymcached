import warnings

from pymcached.__about__ import __version__
from pymcached.models import Data


def run_replace(data_store, arguments: list[str], payload: bytes):
    _, key, flags, expiration_time, number_of_bytes, *noreply = arguments
    if expiration_time != 0:
        warnings.warn("Expiration time is not supported yet", stacklevel=1)

    if key not in data_store:
        return b"NOT_STORED\r\n"

    data = Data(
        payload=payload,
        flags=int(flags),
        expiration_time=int(expiration_time),
        size=int(number_of_bytes),
    )

    data_store[key] = data
    return b"STORED\r\n"


def run_flush_all(data_store, arguments: list[str]):
    _, *noreply = arguments
    data_store.clear()
    return b"OK\r\n"


def run_add(data_store, arguments: list[str], payload: bytes):
    _, key, flags, expiration_time, number_of_bytes, *noreply = arguments
    if expiration_time != 0:
        warnings.warn("Expiration time is not supported yet", stacklevel=1)

    if key in data_store:
        return b"NOT_STORED\r\n"

    data = Data(
        payload=payload,
        flags=int(flags),
        expiration_time=int(expiration_time),
        size=int(number_of_bytes),
    )

    data_store[key] = data
    return b"STORED\r\n"


def run_set(data_store, arguments: list[str], payload: bytes):
    _, key, flags, expiration_time, number_of_bytes, *noreply = arguments
    if expiration_time != 0:
        warnings.warn("Expiration time is not supported yet", stacklevel=1)

    data = Data(
        payload=payload,
        flags=int(flags),
        expiration_time=int(expiration_time),
        size=int(number_of_bytes),
    )

    data_store[key] = data
    return b"STORED\r\n"


def run_get(data_store, keys: list[str]):
    response = b""
    for key in keys:
        if stored_data := data_store.get(key):
            response += (
                f"VALUE {key} {stored_data.flags} {stored_data.size}\r\n".encode()
                + stored_data.payload.encode()
                + b"\r\n"
            )

    response += b"END\r\n"
    return response


def run_delete(data_store, arguments: list[str]):
    _, key, freeze_time, *noreply = arguments
    if freeze_time != 0:
        warnings.warn("'Freeze' time is not supported yet", stacklevel=1)

    if key not in data_store:
        return b"NOT_FOUND\r\n"

    del data_store[key]
    return b"DELETED\r\n"


def run_version(*_):
    return f"VERSION {__version__}\r\n".encode()


def run_incr(data_store, arguments: list[str]):
    _, key, value = arguments

    if key not in data_store:
        return b"NOT_FOUND\r\n"

    if not data_store[key].payload.isdigit():
        data_store[key].payload = 0

    data_store[key].payload = int(data_store[key].payload) + int(value)

    return f"{data_store[key].payload}\r\n".encode()


def run_decr(data_store, arguments: list[str]):
    _, key, value = arguments

    if key not in data_store:
        return b"NOT_FOUND\r\n"

    if not data_store[key].payload.isdigit():
        data_store[key].payload = 0

    data_store[key].payload = int(data_store[key].payload) - int(value)
    if data_store[key].payload < 0:
        data_store[key].payload = 0

    return f"{data_store[key].payload}\r\n".encode()
