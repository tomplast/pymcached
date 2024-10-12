import socket
import pytest


class MemcachedTCPClient:
    def __init__(self, host: str = "localhost", port=11211):
        self._host = host
        self._port = port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        self._socket = s

    def set(self, key: str, value: str):
        self._socket.send(f"set {key} 0 0 {len(value)}\r\n{value}\r\n".encode())
        response = self._socket.recv(1024)
        return response.decode().rstrip("\r\n")

    def add(self, key: str, value: str):
        self._socket.send(f"add {key} 0 0 {len(value)}\r\n{value}\r\n".encode())
        response = self._socket.recv(1024)
        return response.decode().rstrip("\r\n")

    def replace(self, key: str, value: str):
        self._socket.send(f"replace {key} 0 0 {len(value)}\r\n{value}\r\n".encode())
        response = self._socket.recv(1024)
        return response.decode().rstrip("\r\n")

    def get(self, key: str):
        self._socket.send(f"get {key}\r\n".encode())
        response = self._socket.recv(1024)
        return response.split(b"\r\n")[1].decode()

    def flush_all(self):
        self._socket.send(b"flush_all\r\n")
        return self._socket.recv(1024)

    def incr(self, key: str, value: int):
        self._socket.send(f"incr {key} {value}\r\n".encode())
        response = self._socket.recv(1024)
        return int(response.decode().rstrip("\r\n"))

    def decr(self, key: str, value: int):
        self._socket.send(f"decr {key} {value}\r\n".encode())
        response = self._socket.recv(1024)
        return int(response)


@pytest.fixture
def memcached_client():
    client = MemcachedTCPClient()
    client.flush_all()
    yield client
    client.flush_all()


def test_set_get(memcached_client):
    memcached_client.set("key", "value")
    response = memcached_client.get("key")
    assert response == "value"


def test_incr(memcached_client):
    memcached_client.set("key", "0")
    response = memcached_client.incr("key", 5)
    assert response == 5


def test_set_flush_and_get(memcached_client):
    memcached_client.set("key", "value")
    memcached_client.flush_all()
    response = memcached_client.get("key")
    assert response == ""


def test_decr(memcached_client):
    memcached_client.set("key", "5")
    response = memcached_client.decr("key", 2)
    assert response == 3


def test_add(memcached_client):
    memcached_client.add("key", "value")
    response = memcached_client.get("key")
    assert response == "value"


def test_add_with_existing_key(memcached_client):
    memcached_client.set("key", "value")
    response = memcached_client.add("key", "value")
    assert response == "NOT_STORED"


def test_replace(memcached_client):
    memcached_client.set("key", "value")
    response = memcached_client.replace("key", "value2")
    assert response == "STORED"


def test_replace_with_non_existing_key(memcached_client):
    response = memcached_client.replace("key", "value")
    assert response == "NOT_STORED"
