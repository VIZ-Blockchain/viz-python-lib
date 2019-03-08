import re
import logging

from threading import Lock

from vizbase.chains import KNOWN_CHAINS
from grapheneapi.api import Api as Original_Api

from grapheneapi.websocket import Websocket as Original_Websocket
from grapheneapi.rpc import Rpc as Original_Rpc
from grapheneapi.http import Http as Original_Http

from . import exceptions
from .consts import API

log = logging.getLogger(__name__)


class NodeRPC(Original_Api):
    """ Redefine graphene Api class

        API class inheritance:
        viz.Client -> graphenecommon.chain.AbstractGrapheneChain -> vizapi.NodeRPC ->
        grapheneapi.api.Api -> grapheneapi.api.Websocket -> grapheneapi.api.Rpc

        We are overriding here locally Websocket and Rpc classes. We have to override
        Websocket because we need it to inherit from our own Rpc class.

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

    def post_process_exception(self, e):
        msg = exceptions.decodeRPCErrorMsg(e).strip()
        if msg == "missing required active authority":
            raise exceptions.MissingRequiredActiveAuthority
        elif msg == "Internal error: Unable to acquire READ lock":
            raise exceptions.ReadLockFail(msg)
        elif re.match(
            "current_account_itr == acnt_indx.indices().get<by_name>().end()", msg
        ):
            raise exceptions.AccountCouldntBeFoundException(msg)
        elif re.match("Assert Exception: is_valid_name( name )", msg):
            raise exceptions.InvalidAccountNameException(msg)
        elif re.match("^no method with name.*", msg):
            raise exceptions.NoMethodWithName(msg)
        elif msg:
            raise exceptions.UnhandledRPCError(msg)
        else:
            raise e

    def updated_connection(self):
        if self.url[:2] == "ws":
            # Use own Websocket class
            return Websocket(self.url, **self._kwargs)
        elif self.url[:4] == "http":
            return Http(self.url, **self._kwargs)
        else:
            raise ValueError("Only support http(s) and ws(s) connections!")

    def get_network(self):
        """ Cache connected network info

            This avoids multiple calls of self.get_config()
        """
        if self._network:
            return self._network
        self._network = self._get_network()
        return self._network

    def _get_network(self):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        # Cache config into self.config to be accesible as
        # blockchain_instance.rpc.config
        self.config = self.get_config()
        chain_id = self.config["CHAIN_ID"]
        for k, v in KNOWN_CHAINS.items():
            if v["chain_id"] == chain_id:
                return v
        raise Exception("Connecting to unknown network!")


class Rpc(Original_Rpc):
    """ This class is responsible for making RPC queries

        Original graphene chains (like Bitshares) uses api_id in "params", while Golos
        and VIZ uses api name here.
    """

    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        """ Map all methods to RPC calls and pass through the arguments
        """

        def method(*args, **kwargs):
            api = kwargs.get("api", API.get(name))
            if not api:
                raise exceptions.NoSuchAPI(
                    'Cannot find API for you request "{}"'.format(name)
                )

            # Fix wrong api name hardcoded in graphenecommon.TransactionBuilder
            if api == "network_broadcast":
                api = "network_broadcast_api"

            # let's be able to define the num_retries per query
            self.num_retries = kwargs.get("num_retries", self.num_retries)

            query = {
                "method": "call",
                "params": [api, name, list(args)],
                "jsonrpc": "2.0",
                "id": self.get_request_id(),
            }
            log.debug(query)
            while True:
                try:
                    r = self.rpcexec(query)
                    message = self.parse_response(r)
                except exceptions.ReadLockFail:
                    pass
                else:
                    break
            return message

        return method


class Websocket(Original_Websocket, Rpc):
    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)

        ### We don't initializing Original_Websocket, so we need to double it's code

        # We need a lock to ensure thread-safty
        self.__lock = Lock()


class Http(Original_Http, Rpc):
    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)
