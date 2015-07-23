class PluginInitialisationError(Exception):
    pass

class NetworkConnectionError(Exception):
    pass

class RemoteServerError(Exception):
    pass

class MessageInvalidError(Exception):
    pass

class InputDataError(Exception):
    pass

##
# AsyncServerException is used to wrap communication exceptions.

class AsyncServerException(Exception):
    pass