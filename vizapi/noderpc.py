import logging
from threading import Lock

from grapheneapi.api import Api as GrapheneApi
from grapheneapi.http import Http as GrapheneHttp
from grapheneapi.rpc import Rpc as GrapheneRpc
from grapheneapi.websocket import Websocket as GrapheneWebsocket

from vizbase.chains import KNOWN_CHAINS

from . import exceptions
from .consts import API

log = logging.getLogger(__name__)


class NodeRPC(GrapheneApi):
    """
    Redefine graphene Api class.

    Class wraps communications with API nodes via proxying requests to lower-level :py:class:`Rpc` class and it's
    implementations :py:class:`Websocket` and :py:class:`Http`.

    To enable RPC debugging:

    .. code-block:: python

        log = logging.getLogger('vizapi')
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.StreamHandler())
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._network = None
        self.config = None

    def post_process_exception(self, error: Exception) -> None:
        """
        Process error response and raise proper exception.

        Called from :py:meth:`__getattr__`, which catches RPCError exception which raised by
        :py:meth:`Rpc.parse_response` in Rpc class.

        :param error: exception
        """
        if isinstance(error, exceptions.NoSuchAPI):
            raise

        msg = exceptions.decode_rpc_error_msg(error)
        if (
            msg.startswith("Missing Active Authority")
            or msg.startswith("Missing Master Authority")
            or msg.startswith("Missing Authority")
            or msg.startswith("Missing Regular Authority")
        ):
            raise exceptions.MissingRequiredAuthority(msg)
        elif msg == "Unable to acquire READ lock":
            raise exceptions.ReadLockFail(msg)
        elif msg:
            raise exceptions.UnhandledRPCError(msg)
        else:
            raise error

    def updated_connection(self):
        if self.url[:2] == "ws":
            # Use own Websocket class
            return Websocket(self.url, **self._kwargs)
        elif self.url[:4] == "http":
            return Http(self.url, **self._kwargs)
        else:
            raise ValueError("Only support http(s) and ws(s) connections!")

    def get_network(self):
        """
        Cache connected network info.

        This avoids multiple calls of self.get_config()
        """
        if self._network:
            return self._network
        self._network = self._get_network()
        return self._network

    def _get_network(self):
        """
        Identify the connected network.

        This call returns a dictionary with keys chain_id, core_symbol and prefix
        """
        # Cache config into self.config to be accesible as
        # blockchain_instance.rpc.config
        self.config = self.get_config()
        chain_id = self.config["CHAIN_ID"]
        for _, chain_data in KNOWN_CHAINS.items():
            if chain_data["chain_id"] == chain_id:
                return chain_data
        raise exceptions.UnknownNetwork("Connecting to unknown network!")


class Rpc(GrapheneRpc):
    """
    This class is responsible for making RPC queries.

    Original graphene chains (like Bitshares) uses api_id in "params", while Golos and VIZ uses api name here.
    """

    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""

        def method(*args, **kwargs):
            api = kwargs.get("api", API.get(name))
            if not api:
                raise exceptions.NoSuchAPI('Cannot find API for you request "{}"'.format(name))

            # Fix wrong api name hardcoded in graphenecommon.TransactionBuilder
            if api == "network_broadcast":
                api = "network_broadcast_api"

            query = {
                "method": "call",
                "params": [api, name, list(args)],
                "jsonrpc": "2.0",
                "id": self.get_request_id(),
            }
            log.debug(query)
            while True:
                try:
                    response = self.rpcexec(query)
                    message = self.parse_response(response)
                except exceptions.ReadLockFail:
                    pass
                else:
                    break
            return message

        return method


class Websocket(GrapheneWebsocket, Rpc):
    """
    Interface to API node websocket endpoint.

    We have to override Websocket class because we need it to inherit from our own Rpc class.
    """

    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)

        # We don't initializing GrapheneWebsocket, so we need to double it's code

        # We need a lock to ensure thread-safty
        self.__lock = Lock()


class Http(GrapheneHttp, Rpc):
    """
    Interface to API node http endpoint.

    We have to override Websocket class because we need it to inherit from our own Rpc class.
    """

    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)
