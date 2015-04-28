#!/usr/bin/env python

# pylint: disable=broad-except

import os, sys, time, signal
import logging
import logging.handlers
import yaml
import datetime

import getopt
from getopt import GetoptError

from daemon import Daemon
from reporting.utilities import getLogger, excepthook, get_log_level
from reporting.__version__ import version
from reporting.outputs import KafkaHTTPOutput, BufferOutput
from reporting.pusher import Pusher
from reporting.collectors import Collector
from __builtin__ import True

log = getLogger("producer")

class ProducerDaemon(Daemon):
    def __init__(self, pidfile, config, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)
        self.__running=True
        self.config=config
        self.__outputs={}
        self.__pusher_pid=-1
        self.__collectors=[]
        
    def __sigTERMhandler(self, signum, frame):
        log.debug("Caught signal %d. Exiting" % signum)
        self.quit()
        
    def quit(self):
        for c in self.__collectors:
            c.quit()
        if self.__pusher_pid>-1:
            try:
                os.kill(self.__pusher_pid, signal.SIGTERM)
            except OSError, err:
                err = str(err)
                if err.find("No such process") > 0:
                    log.info("Pusher process has gone.")
        self.__running=False

    def init(self):
        if 'buffer' in config['output']:
            if not 'directory' in config['output']['buffer']:
                print("ERROR: buffer directory not specified in config.")
                return False
            buffer_dir=config['output']['buffer']['directory']
            if os.path.exists(buffer_dir) and (not os.path.isdir(buffer_dir)):
                print("ERROR: buffer directory exists but it is not a directory.")
                return False
            if not os.path.exists(buffer_dir):
                log.info("Creating buffer directory %s." % buffer_dir)
                os.makedirs(buffer_dir)
            self.__outputs['buffer']=BufferOutput(config["output"]['buffer'])
        if 'kafka-http' in config['output']:
            self.__outputs['kafka-http']=KafkaHTTPOutput(config["output"]['kafka-http'])
        if 'pusher' in config:
            if not 'directory' in config['pusher'] or not 'output' in config['pusher']:
                print("ERROR: need to speficity directory and output in pusher.")
                return False
        return True
        
    def run(self):
        # Install signal handlers
        signal.signal(signal.SIGTERM, self.__sigTERMhandler)
        signal.signal(signal.SIGINT, self.__sigTERMhandler)
        # Ensure unhandled exceptions are logged
        sys.excepthook = excepthook
        log.warning("Reporting producer started at %s" % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        if 'pusher' in config:
            pusher=Pusher(self.__outputs[config['pusher']['output']], config['pusher']['directory'])
            pusher.daemon=True
            pusher.start()
            self.__pusher_pid=pusher.pid
            log.info("started pusher pid=%d" % pusher.pid)
        if 'collector' in config:
            for collector_config in config['collector']:
                log.debug("initiating collector %s"%collector_config)
                log.debug("self.__outputs %s"%self.__outputs)
                c=Collector(collector_config, config['collector'][collector_config], self.__outputs[config['collector'][collector_config]['output']])
                self.__collectors.append(c)
        for c in self.__collectors:
            c.start()
        if 'buffer' in self.__outputs:
            while self.__running:
                self.__outputs['buffer'].execute()
                time.sleep(1)
            self.__outputs['buffer'].cleanup()
        if 'pusher' in config:
            pusher.join()
        for c in self.__collectors:
            if c.is_alive():
                c.join()
        log.warning("Reporting producer stopped at %s" % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
            
def usage():
    """ Prints reporting producer command line options and exits
    """
    print "Usage: %s [OPTIONS]" % sys.argv[0]
    print
    print "Reporting Producer v" + version + " manages local producers and buffer/pusher."
    print
    print "Options:"
    print "    -b                   start in background"
    print "    -f                   start in foreground"
    print "    -k                   kill a background instance"
    print "    -v                   verbose level: -v, warning; -vv, info; -vvv, debug. It will be overwritten by the setting in config file."
    print "    -p <FILE>            pidfile path"
    print "    -c <FILE>            configuration file path"
    print "    -h, --help           display this help message"
    print "    -V, --version        print the version"
    
if __name__ == "__main__":
    try:
        (opts, getopts) = getopt.getopt(sys.argv[1:], 'bfvp:c:khV',
                                        ["background", "foreground", "verbose", "pid=",
                                         "config=", "kill", "help", "version"])
    except GetoptError:
        print "\nInvalid command line option detected."
        usage()
        sys.exit(1)
    daemon=False
    verbose=0
    killing=False
    pid_file="/tmp/daemon-producer.pid"
    config_file="config.yaml"
    #print opts
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-b', '--background'):
            daemon=True
        if opt in ('-f', '--foreground'):
            daemon=False
        if opt in ('-k', '--kill'):
            killing=True
        if opt in ('-p', '--pid'):
            pid_file = arg
        if opt in ('-c', '--config'):
            config_file = arg
        if opt in ('-v', '--verbose'):
            verbose += 1
        if opt in ('-V', '--version'):
            print "Reporting Producer version:", version
            sys.exit(0)    
    
    if not os.path.exists(config_file) or not os.path.isfile(config_file):
        print "Config file %s does not exist or is not a file." % config_file
        sys.exit(1)
        
    config = yaml.load(open(config_file, "r"))
    producer = ProducerDaemon(pid_file, config)
    if 'logging' in config:
        if 'log_level' in config['logging']:
            log.setLevel(get_log_level(config['logging']['log_level']))
        if daemon==False:
            # Add the default logging handler to dump to stderr
            logout = logging.StreamHandler(sys.stderr)
            # set a format which is simpler for console use
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(threadName)s - %(message)s')
            # tell the handler to use this format
            logout.setFormatter(formatter)
            log.addHandler(logout)
        elif daemon==True and killing==False:
            log_formatter = logging.Formatter(config['logging']['log_format'])
            file_handler = None
            if 'log_max_size' in config['logging']:
                file_handler = logging.handlers.RotatingFileHandler(
                                                config['logging']['log_location'],
                                                maxBytes=config['logging']['log_max_size'],
                                                backupCount=3)
            else:
                try:
                    file_handler = logging.handlers.WatchedFileHandler(
                                                config['logging']['log_location'],)
                except AttributeError:
                    # Python 2.5 doesn't support WatchedFileHandler
                    file_handler = logging.handlers.RotatingFileHandler(
                                                config['logging']['log_location'],)
    
            file_handler.setFormatter(log_formatter)
            log.addHandler(file_handler)
    if verbose>0:
        log.setLevel(get_log_level(verbose))
    #print "daemon %s killing %s" % (daemon, killing)
    if killing==True:
        producer.stop()
        sys.exit(0)
    if not producer.init():
        print "init failed."
        sys.exit(1)
    if daemon==True:
        producer.start()
    elif daemon==False:
        producer.run()
    sys.exit(0)
