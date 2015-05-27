import asyncore, asynchat, socket, os, sys, fcntl, traceback

from reporting.utilities import getLogger, formatExceptionInfo
from reporting.exceptions import AsyncServerException
log = getLogger(__name__)

##
# Request handler class.
#
# This class extends asynchat in order to provide a request handler for
# incoming query.

class RequestHandler(asynchat.async_chat):
    
    END_STRING = "\n"

    def __init__(self, conn, producer):
        asynchat.async_chat.__init__(self, conn)
        self.__producer = producer
        self.__buffer = []
        # Sets the terminator.
        self.set_terminator(RequestHandler.END_STRING)

    def collect_incoming_data(self, data):
        #log.debug("Received raw data: " + str(data))
        self.__buffer.append(data)

    ##
    # Handles a new request.
    #
    # This method is called once we have a complete request.

    def found_terminator(self):
        # Joins the buffer items.
        input_msg = ''.join(self.__buffer)
        log.debug("Received input data: " + str(input_msg))
        # Gives the message to the transmitter.
        output_msg = self.__producer.console(input_msg)
        # Sends the response to the client.
        self.push(output_msg)
        # Closes the channel.
        self.close_when_done()
        
    def handle_error(self):
        e1, e2 = formatExceptionInfo()
        log.error("Unexpected communication error: %s" % str(e2))
        log.error(traceback.format_exc().splitlines())
        self.close()
        
##
# Asynchronous server class.
#
# This class extends asyncore and dispatches connection requests to
# RequestHandler.

class AsyncServer(asyncore.dispatcher):

    def __init__(self, producer, sock_file="/tmp/socket.file"):
        asyncore.dispatcher.__init__(self)
        self.__producer = producer
        self.__sock = sock_file
        self.__init = False

    ##
    # Returns False as we only read the socket first.

    def writable(self):
        return False

    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            log.warning("Socket error")
            return
        except TypeError:
            log.warning("Type error")
            return
        AsyncServer.__markCloseOnExec(conn)
        # Creates an instance of the handler class to handle the
        # request/response on the incoming connection.
        RequestHandler(conn, self.__producer)
    
    ##
    # Starts the communication server.
    #
    # @param sock: socket file.
    # @param force: remove the socket file if exists.
    
    def start(self, sock, force=True):
        self.__sock = sock
        # Remove socket
        if os.path.exists(sock):
            log.error("Socket file exists")
            if force:
                log.warning("Forcing execution of the server")
                os.remove(sock)
            else:
                raise AsyncServerException("Server already running")
        # Creates the socket.
        self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.set_reuse_addr()
        try:
            self.bind(sock)
        except Exception:
            raise AsyncServerException("Unable to bind socket %s" % self.__sock)
        AsyncServer.__markCloseOnExec(self.socket)
        self.listen(1)
        # Sets the init flag.
        self.__init = True
        # TODO Add try..catch
        # There's a bug report for Python 2.6/3.0 that use_poll=True yields some 2.5 incompatibilities:
        if (sys.version_info >= (2, 7) and sys.version_info < (2, 8)) \
           or (sys.version_info >= (3, 4)): # if python 2.7 ...
            log.debug("Detected Python 2.7. asyncore.loop() using poll")
            asyncore.loop(use_poll=True) # workaround for the "Bad file descriptor" issue on Python 2.7, gh-161
        else:
            asyncore.loop(use_poll=False) # fixes the "Unexpected communication problem" issue on Python 2.6 and 3.0
    
    ##
    # Stops the communication server.
    
    def stop(self):
        if self.__init:
            # Only closes the socket if it was initialized first.
            self.close()
        # Remove socket
        if os.path.exists(self.__sock):
            log.info("Removed socket file " + self.__sock)
            os.remove(self.__sock)
        log.debug("Socket shutdown")

    ##
    # Marks socket as close-on-exec to avoid leaking file descriptors when
    # running actions involving command execution.

    # @param sock: socket file.
    
    @staticmethod
    def __markCloseOnExec(sock):
        fd = sock.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags|fcntl.FD_CLOEXEC)
