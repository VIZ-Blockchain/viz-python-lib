import re

from threading import Lock

from vizbase.chains import known_chains
from grapheneapi.api import Api as Original_Api

from grapheneapi.websocket import Websocket as Original_Websocket
from grapheneapi.rpc import Rpc as Original_Rpc
from grapheneapi.http import Http as Original_Http

from . import exceptions
from .consts import API


class NodeRPC(Original_Api):
    """ Redefine graphene Api class

        API class inheritance:
        viz.Client -> graphenecommon.chain.AbstractGrapheneChain -> vizapi.NodeRPC ->
        grapheneapi.api.Api -> grapheneapi.api.Websocket -> grapheneapi.api.Rpc

        We are overriding here locally Websocket and Rpc classes. We have to override
        Websocket because we need it to inherit from our own Rpc class.
    """

    def post_process_exception(self, e):
        msg = exceptions.decodeRPCErrorMsg(e).strip()
        if msg == "missing required active authority":
            raise exceptions.MissingRequiredActiveAuthority
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
            return Original_Http(self.url, **self._kwargs)
        else:
            raise ValueError("Only support http(s) and ws(s) connections!")

    def get_network(self):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        props = self.get_chain_properties()
        chain_id = props["chain_id"]
        for k, v in known_chains.items():
            if v["chain_id"] == chain_id:
                return v
        raise Exception("Connecting to unknown network!")

    def get_account(self, name, **kwargs):
        """ Get full account details from account name or id

            :param str name: Account name or account id
        """
        if len(name.split(".")) == 3:
            return self.get_objects([name])[0]
        else:
            return self.get_account_by_name(name, **kwargs)

    def get_asset(self, name, **kwargs):
        """ Get full asset from name of id

            :param str name: Symbol name or asset id (e.g. 1.3.0)
        """
        if len(name.split(".")) == 3:
            return self.get_objects([name], **kwargs)[0]
        else:
            return self.lookup_asset_symbols([name], **kwargs)[0]

    def get_object(self, o, **kwargs):
        """ Get object with id ``o``

            :param str o: Full object id
        """
        return self.get_objects([o], **kwargs)[0]


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
            api = kwargs.get('api', API[name])

            # let's be able to define the num_retries per query
            self.num_retries = kwargs.get("num_retries", self.num_retries)

            query = {
                "method": "call",
                "params": [api, name, list(args)],
                "jsonrpc": "2.0",
                "id": self.get_request_id(),
            }
            r = self.rpcexec(query)
            message = self.parse_response(r)
            return message

        return method


class Websocket(Original_Websocket, Rpc):
    def __init__(self, *args, **kwargs):
        super(Rpc, self).__init__(*args, **kwargs)

        ### We don't initializing Original_Websocket, so we need to double it's code

        # We need a lock to ensure thread-safty
        self.__lock = Lock()
