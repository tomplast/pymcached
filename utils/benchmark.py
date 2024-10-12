import logging
import time

from pymemcache.client import base

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.INFO)
logging.basicConfig(
    handlers=[console_logger],
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# Configure the memcached client to connect to your local Memcached server
client = base.Client(("localhost", 11211))


def benchmark_set_operation(iterations=1000000):
    start_time = time.time()
    for i in range(iterations):
        key = f"key{i}"
        value = f"value{i}"
        client.set(key, value)
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(
        f"Set operation: {iterations} iterations took {total_time:.4f} seconds, average time per operation: {total_time / iterations:.6f} seconds"
    )


def benchmark_get_operation(iterations=1000000):
    # Ensure all keys exist before the get benchmark
    for i in range(iterations):
        key = f"key{i}"
        value = f"value{i}"
        client.set(key, value)

    start_time = time.time()
    for i in range(iterations):
        key = f"key{i}"
        client.get(key)
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(
        f"Get operation: {iterations} iterations took {total_time:.4f} seconds, average time per operation: {total_time / iterations:.6f} seconds"
    )


# Run the benchmarks
benchmark_set_operation()
benchmark_get_operation()

# Close the client connection
client.close()
