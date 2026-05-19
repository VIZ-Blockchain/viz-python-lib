import logging
import warnings
from threading import Lock

from grapheneapi.api import Api as GrapheneApi
from grapheneapi.http import Http as GrapheneHttp
from grapheneapi.rpc import Rpc as GrapheneRpc
from grapheneapi.websocket import Websocket as GrapheneWebsocket

from vizbase.chains import KNOWN_CHAINS
from vizbase.validator_compat import API_METHOD_ALIASES

from . import exceptions
from .consts import API

log = logging.getLogger(__name__)

# Reverse map for runtime fallback: new method name -> old method name.
_REVERSE_API_METHOD = {new: old for old, new in API_METHOD_ALIASES.items()}


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
        msg_lower = msg.lower()
        if (
            msg.startswith("Missing Active Authority")
            or msg.startswith("Missing Master Authority")
            or msg.startswith("Missing Authority")
            or msg.startswith("Missing Regular Authority")
        ):
            raise exceptions.MissingRequiredAuthority(msg)
        elif msg == "Unable to acquire READ lock":
            raise exceptions.ReadLockFail(msg)
        elif "could not find method" in msg_lower or "method not found" in msg_lower or "no such method" in msg_lower:
            raise exceptions.NoSuchMethod(msg)
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

    Phase A of the witness -> validator migration: inbound calls using old
    method names are translated to new names with a DeprecationWarning.
    On a NoSuchMethod error against the new method, the dispatcher falls
    back to the old method on `witness_api` and caches the result so
    subsequent calls skip the new-name attempt.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # None = unknown; True = node only knows witness_api; False = new names confirmed.
        self._uses_legacy_witness_api: bool | None = None

    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""

        def method(*args, **kwargs):
            # Inbound translation: if caller used a deprecated witness_* name,
            # translate to the validator_* equivalent and warn.
            canonical_name = API_METHOD_ALIASES.get(name, name)
            if canonical_name != name:
                warnings.warn(
                    f"API method '{name}' is deprecated; use '{canonical_name}' instead",
                    DeprecationWarning,
                    stacklevel=2,
                )

            api = kwargs.get("api", API.get(canonical_name))
            if not api:
                raise exceptions.NoSuchAPI(f'Cannot find API for you request "{canonical_name}"')

            # Fix wrong api name hardcoded in graphenecommon.TransactionBuilder
            if api == "network_broadcast":
                api = "network_broadcast_api"

            # If the node is known to only speak witness_api, skip new-name attempt.
            if self._uses_legacy_witness_api and canonical_name in _REVERSE_API_METHOD:
                return self._call_legacy(canonical_name, list(args))

            return self._call_with_fallback(api, canonical_name, list(args))

        return method

    def _call_legacy(self, canonical_name: str, params_args: list) -> object:
        old_name = _REVERSE_API_METHOD[canonical_name]
        return self._do_call("witness_api", old_name, params_args)

    def _call_with_fallback(self, api: str, canonical_name: str, params_args: list) -> object:
        try:
            result = self._do_call(api, canonical_name, params_args)
        except exceptions.NoSuchMethod:
            if canonical_name not in _REVERSE_API_METHOD:
                raise
            if self._uses_legacy_witness_api is None:
                warnings.warn(
                    "Node responded on witness_api; upgrade recommended",
                    DeprecationWarning,
                    stacklevel=4,
                )
            self._uses_legacy_witness_api = True
            return self._call_legacy(canonical_name, params_args)
        else:
            if self._uses_legacy_witness_api is None:
                self._uses_legacy_witness_api = False
            return result

    def _do_call(self, api: str, name: str, params_args: list) -> object:
        query = {
            "method": "call",
            "params": [api, name, params_args],
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
