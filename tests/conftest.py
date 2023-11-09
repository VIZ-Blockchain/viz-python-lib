import logging
import socket
import uuid
import docker
import pytest

from viz import Client
from viz.instance import set_shared_chain_instance

log = logging.getLogger("vizapi")
log.setLevel(logging.DEBUG)


@pytest.fixture(scope="session")
def private_keys():
    return [
        "5JabcrvaLnBTCkCVFX5r4rmeGGfuJuVp4NAKRNLTey6pxhRQmf4",
        "5Hw9YPABaFxa2LooiANLrhUK5TPryy8f7v9Y1rk923PuYqbYdfC",
        "5J9DBCRX5D2ZUUuy9qV2ef9p5sfA3ydHsDs2G531bob7wbEigDJ",
    ]


@pytest.fixture(scope="session")
def default_account():
    return "viz"


@pytest.fixture(scope="session")
def session_id():
    """
    Generate unique session id.

    This is needed in case testsuite may run in parallel on the same server, for example if CI/CD is being used. CI/CD
    infrastructure may run tests for each commit, so these tests should not influence each other.
    """
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def unused_port():
    """Obtain unused port to bind some service."""

    def _unused_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    return _unused_port


@pytest.fixture(scope="session")
def docker_manager():
    """Initialize docker management client."""
    return docker.from_env(version="auto")


@pytest.fixture(scope="session")
def viz_testnet(session_id, unused_port, docker_manager):
    """Run vizd inside local docker container."""
    port_http = unused_port()
    port_ws = unused_port()
    container = docker_manager.containers.run(
        image="vizblockchain/vizd:testnet",
        name="viz-testnet-{}".format(session_id),
        ports={"8090": port_http, "8091": port_ws},
        detach=True,
    )
    container.http_port = port_http
    container.ws_port = port_ws
    
    yield container
    container.remove(v=True, force=True)


@pytest.fixture(scope="session")
def viz_instance_ws(viz_testnet, private_keys):
    """Initialize BitShares instance connected to a local testnet."""
    viz = Client(node="ws://127.0.0.1:{}".format(viz_testnet.ws_port), keys=private_keys, num_retries=-1)
    set_shared_chain_instance(viz)

    return viz


@pytest.fixture(scope="session")
def viz(viz_instance_ws):
    """Shortcut to ws instance."""

    return viz_instance_ws
