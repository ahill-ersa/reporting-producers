#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.plugins.pbs import AccountingLogParser, ServerLogParser, MomLogParser
from reporting.plugins.xfs import QuotaReportParser
from reporting.plugins.nfs import MountstatsParser
import json
import sys

class ExamplePresenter():
    def show_pbs_accouting_log(object):
        parser=AccountingLogParser()
        input=["05/01/2015 00:29:15;Q;27570.emuheadnode.cloud.ersa.edu.au;queue=emu",
               "05/01/2015 00:29:15;E;27542.emuheadnode.cloud.ersa.edu.au;user=mpenna group=mpenna jobname=pull.16.sh queue=emu ctime=1430377782 qtime=1430377783 etime=1430377783 start=1430390087 owner=mpenna@cw-vm-d195.sa.nectar.org.au exec_host=cw-vm-d144.sa.nectar.org.au/7+cw-vm-d144.sa.nectar.org.au/6+cw-vm-d144.sa.nectar.org.au/5+cw-vm-d144.sa.nectar.org.au/4+cw-vm-d144.sa.nectar.org.au/3+cw-vm-d144.sa.nectar.org.au/2+cw-vm-d144.sa.nectar.org.au/1+cw-vm-d145.sa.nectar.org.au/0-3 Resource_List.mem=4gb Resource_List.neednodes=1:ppn=8 Resource_List.nodect=1 Resource_List.nodes=1:ppn=8 Resource_List.walltime=10:00:00 session=21825 end=1430405955 Exit_status=0 resources_used.cput=00:00:10 resources_used.mem=3348kb resources_used.vmem=54768kb resources_used.walltime=04:24:28"]
        for i in input:
            print pretty_print(parser.parse(i))
    def show_pbs_server_log(object):
        parser=ServerLogParser()
        input=["05/06/2015 15:20:05;000d;PBS_Server.2629;Job;28091.emuheadnode.cloud.ersa.edu.au;preparing to send 'e' mail for job 28091.emuheadnode.cloud.ersa.edu.au to mpenna@cw-vm-d195.sa.nectar.org.au (Exit_status=0",
                "05/06/2015 15:20:05;000d;PBS_Server.2629;Job;28091.emuheadnode.cloud.ersa.edu.au;Not sending email: User does not want mail of this type.",
                "05/06/2015 15:20:05;0010;PBS_Server.2629;Job;28091.emuheadnode.cloud.ersa.edu.au;Exit_status=0 resources_used.cput=00:00:10 resources_used.mem=3356kb resources_used.vmem=54776kb resources_used.walltime=04:18:43",
                "05/06/2015 15:20:05;0009;PBS_Server.2629;Job;28091.emuheadnode.cloud.ersa.edu.au;on_job_exit task assigned to job",
                "05/06/2015 15:20:05;0009;PBS_Server.2629;Job;28091.emuheadnode.cloud.ersa.edu.au;req_jobobit completed",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;28091.emuheadnode.cloud.ersa.edu.au;on_job_exit valid pjob: 28091.emuheadnode.cloud.ersa.edu.au (substate=50)",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;handle_exiting_or_abort_substate;28091.emuheadnode.cloud.ersa.edu.au; JOB_SUBSTATE_EXITING",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;28091.emuheadnode.cloud.ersa.edu.au;about to copy stdout/stderr/stageout files",
                "05/04/2015 23:38:36;0100;PBS_Server;Job;1126029.tizard1;enqueuing into tizard, state 1 hop 1",
                "05/04/2015 23:38:36;0008;PBS_Server;Job;1126029.tizard1;Job Queued at request of mpenna@tizard1, owner = mpenna@tizard1, job name = pull.8.sh, queue = tizard",
                "05/04/2015 23:28:18;0008;PBS_Server;Job;NULL;on_job_exit valid pjob: 0x1d0b5d740 (substate=50)",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;handle_exited;28091.emuheadnode.cloud.ersa.edu.au; JOB_SUBSTATE_EXITED",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;svr_setjobstate;svr_setjobstate: setting job 28091.emuheadnode.cloud.ersa.edu.au state from EXITING-ABORT to COMPLETE-COMPLETE (6-59)",
                "05/06/2015 15:20:05;0008;PBS_Server.4760;Job;28091.emuheadnode.cloud.ersa.edu.au;JOB_SUBSTATE_COMPLETE",
                "05/06/2015 15:20:05;0100;PBS_Server.4760;Job;28091.emuheadnode.cloud.ersa.edu.au;dequeuing from emu, state COMPLETE",
                "05/06/2015 15:20:06;0008;PBS_Server.5425;Job;dispatch_request;dispatching request AuthenticateUser on sd=7",
                "05/04/2015 23:28:19;0008;PBS_Server;Job;1109898.tizard1;Job deleted at request of maui@tizard1",
                "05/06/2015 15:20:06;0008;PBS_Server.5426;Job;dispatch_request;dispatching request StatusJob on sd=6",
                "05/04/2015 23:28:18;0080;PBS_Server;Req;req_reject;Reject reply code=15004(Invalid request MSG=job cancel in progress), aux=0, type=DeleteJob, from maui@tizard1",
                "05/06/2015 15:20:06;0080;PBS_Server.5426;Req;dis_request_read;decoding command StatusJob from root",
                "05/06/2015 15:20:06;0100;PBS_Server.5426;Req;;Type StatusJob request received from root@cw-vm-d294.sa.nectar.org.au, sock=6",
                "05/06/2015 15:20:05;0080;PBS_Server.2117;Req;dis_request_read;decoding command StatusJob from pbs_mom",
                "05/06/2015 15:20:05;0100;PBS_Server.2117;Req;;Type StatusJob request received from pbs_mom@cw-vm-d083.sa.nectar.org.au, sock=6",
                "05/06/2015 15:34:05;0004;PBS_Server.2123;Svr;svr_is_request;message STATUS (4) received from mom on host cw-vm-d144.sa.nectar.org.au (130.220.209.68:360) (sock 6)",
                "05/06/2015 15:34:05;0004;PBS_Server.2123;Svr;svr_is_request;IS_STATUS received from cw-vm-d144.sa.nectar.org.au",
                "05/06/2015 15:34:07;0004;PBS_Server.5428;Svr;svr_connect;attempting connect to host 130.220.209.228 port 15002",
                "05/06/2015 15:34:07;0004;PBS_Server.4759;Svr;check_nodes_work;verifying nodes are active (min_refresh = 10 seconds)",
                "05/04/2015 23:59:09;0001;PBS_Server;Svr;PBS_Server;LOG_ERROR::job nanny, exiting job '1109898.tizard1' still exists, sending a SIGKILL",
                "05/06/2015 15:34:07;0004;PBS_Server.4759;Svr;svr_connect;attempting connect to host 130.220.208.153 port 15002",
                "05/05/2015 00:00:03;0002;PBS_Server;Svr;Log;Log closed",
                "05/04/2015 23:48:05;0040;PBS_Server;Svr;tizard1;Scheduler was sent the command term",
                "05/04/2015 23:52:00;0002;PBS_Server;Svr;PBS_Server;Torque Server Version = 3.0.5, loglevel = 0"]
        for i in input:
            print pretty_print(parser.parse(i))
    def show_pbs_mom_log(object):
        parser=MomLogParser()
        input=["05/04/2015 18:06:01;0080;   pbs_mom.2137;Job;27912.emuheadnode.cloud.ersa.edu.au;scan_for_terminated: job 27912.emuheadnode.cloud.ersa.edu.au task 1 terminated, sid=26219",
                "05/04/2015 18:06:01;0008;   pbs_mom.2137;Job;27912.emuheadnode.cloud.ersa.edu.au;job was terminated",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Svr;preobit_reply;top of preobit_reply",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Svr;preobit_reply;DIS_reply_read/decode_DIS_replySvr worked, top of while loop",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Svr;preobit_reply;in while loop, no error from job stat",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Job;27912.emuheadnode.cloud.ersa.edu.au;obit sent to server",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Job;27912.emuheadnode.cloud.ersa.edu.au;removing transient job directory /mnt/tmp/27912.emuheadnode.cloud.ersa.edu.au",
                "05/04/2015 18:06:01;0080;   pbs_mom.2137;Job;27912.emuheadnode.cloud.ersa.edu.au;removed job script",
                "05/04/2015 18:06:10;0001;   pbs_mom.2137;Job;TMomFinalizeJob3;job 27934.emuheadnode.cloud.ersa.edu.au started, pid = 2053",
                "05/04/2015 18:08:36;0002;   pbs_mom.2137;Svr;pbs_mom;Torque Mom Version = 4.1.7, loglevel = 0",
                "03/11/2015 15:48:45;0080;   pbs_mom;Job;1086553.tizard1;scan_for_terminated: job 1086553.tizard1 task 1 terminated, sid=51441",
                "03/11/2015 15:48:45;0008;   pbs_mom;Job;1086553.tizard1;job was terminated",
                "03/11/2015 15:48:45;0080;   pbs_mom;Svr;preobit_reply;top of preobit_reply",
                "03/11/2015 15:48:45;0080;   pbs_mom;Svr;preobit_reply;DIS_reply_read/decode_DIS_replySvr worked, top of while loop",
                "03/11/2015 15:48:45;0080;   pbs_mom;Svr;preobit_reply;in while loop, no error from job stat",
                "03/11/2015 15:48:45;0080;   pbs_mom;Job;1086553.tizard1;obit sent to server",
                "03/11/2015 15:48:45;0080;   pbs_mom;Job;1086553.tizard1;removed job script",
                "03/11/2015 15:48:46;0001;   pbs_mom;Svr;pbs_mom;LOG_DEBUG::mom_checkpoint_job_has_checkpoint, FALSE",
                "03/11/2015 15:48:46;0001;   pbs_mom;Job;TMomFinalizeJob3;job 1086567.tizard1 started, pid = 59737",
                "03/11/2015 15:49:33;0002;   pbs_mom;Svr;pbs_mom;Torque Mom Version = 3.0.4, loglevel = 0"]
        for i in input:
            print pretty_print(parser.parse(i))
    def show_xfs_quota_report(object):
        parser=QuotaReportParser(exclude_users=["root","nobody","nfsnobody"])
        input=["User quota on /home/users (/dev/sda)",
                "                               Blocks                     ",
                "User ID          Used       Soft       Hard    Warn/Grace     ",
                "---------- -------------------------------------------------- ",
                "root            27280          0          0     00 [--------]",
                "nobody           3404          0          0     00 [--------]",
                "nfsnobody           0      40960      51200     00 [--------]",
                "shundezh      2540188   47185920   52428800     00 [--------]",
                "klara               0   41943040   52428800     00 [--------]",
                "sian                0   41943040   52428800     00 [--------]",
                "mhoward            52   47185920   52428800     00 [--------]",
                "wmenz               0   41943040   52428800     00 [--------]",
                "asquared            0   41943040   52428800     00 [--------]"]
        print pretty_print(parser.parse("\n".join(input)))
    def show_nfs_mountstats(object):
        parser=MountstatsParser(fstype=["nfs","nfs4"])
        input= \
"""
device sunrpc mounted on /var/lib/nfs/rpc_pipefs with fstype rpc_pipefs
device emunfs.cloud.ersa.edu.au:/home/users/ mounted on /home/users with fstype nfs4 statvers=1.0
    opts:    rw,vers=4,rsize=32768,wsize=32768,namlen=255,acregmin=3,acregmax=60,acdirmin=30,acdirmax=60,soft,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,clientaddr=130.220.210.166,minorversion=0,local_lock=none
    age:    5366645
    caps:    caps=0xffff,wtmult=512,dtsize=32768,bsize=0,namlen=255
    nfsv4:    bm0=0xfdffbfff,bm1=0xf9be3e,acl=0x3
    sec:    flavor=1,pseudoflavor=1
    events:    49046 172884523 13215088 27700296 524 10692 292022123 205007498 202 13255586 25953103 106920759 1049 13230888 39677614 39677732 982 39684383 0 3149 191746776 0 0 0 0 0 0 
    bytes:    344623646258 51399162292 0 0 20761165634 53502552035 17454204 25953103 
    RPC iostats version: 1.0  p/v: 100003/4 (nfs)
    xprt:    tcp 834 0 10 0 48 136753376 136753352 0 314402667 0
    per-op statistics
            NULL: 0 0 0 0 0 0 0 0
            READ: 13745489 13745489 0 2474693724 21625405232 181085 7089389 7451549
           WRITE: 15618104 15618111 0 56669809844 2061589408 15720224 46042131 62030231
          COMMIT: 13761718 13761721 0 2477825920 1706453032 633681 54928784 55801930
            OPEN: 39680898 39680898 0 10476367688 15872333096 25445229 19145724 45215679
    OPEN_CONFIRM: 2592 2592 0 466684 176256 36 4662 4747
     OPEN_NOATTR: 0 0 0 0 0 0 0 0
    OPEN_DOWNGRADE: 0 0 0 0 0 0 0 0
           CLOSE: 39680704 39680704 0 7460065216 5237852928 2654369 9178158 12275457
         SETATTR: 13233705 13233706 0 2699755136 3070143992 70089 17109582 19351826
          FSINFO: 1 1 0 148 108 0 0 0
           RENEW: 0 0 0 0 0 0 0 0
     SETCLIENTID: 0 0 0 0 0 0 0 0
    SETCLIENTID_CONFIRM: 0 0 0 0 0 0 0 0
            LOCK: 347 347 0 83200 23596 6 756 770
           LOCKT: 0 0 0 0 0 0 0 0
           LOCKU: 347 347 0 69320 23596 5 1203 1216
          ACCESS: 118574 118574 0 20450956 26745640 1089 677963 722500
         GETATTR: 49047 49049 0 8246364 10190476 128137 373170 550552
          LOOKUP: 37140 37140 0 7496768 8019412 241 79784 83731
     LOOKUP_ROOT: 0 0 0 0 0 0 0 0
          REMOVE: 8063 8063 0 1565560 1899048 25 28653 29217
          RENAME: 9088 9088 0 2646488 3962368 45 27668 28322
            LINK: 0 0 0 0 0 0 0 0
         SYMLINK: 0 0 0 0 0 0 0 0
          CREATE: 561 561 0 146748 269024 5 946 979
        PATHCONF: 1 1 0 144 72 0 0 0
          STATFS: 89597 89600 0 13619200 10393252 107351 576927 771350
        READLINK: 0 0 0 0 0 0 0 0
         READDIR: 1426 1426 0 275100 4859744 8 7863 8003
     SERVER_CAPS: 2 2 0 288 176 0 0 0
     DELEGRETURN: 3601 3601 0 681888 772388 59 48061 51034
          GETACL: 0 0 0 0 0 0 0 0
          SETACL: 0 0 0 0 0 0 0 0
    FS_LOCATIONS: 0 0 0 0 0 0 0 0
    RELEASE_LOCKOWNER: 347 347 0 48572 15268 4 738 768
     EXCHANGE_ID: 0 0 0 0 0 0 0 0
    CREATE_SESSION: 0 0 0 0 0 0 0 0
    DESTROY_SESSION: 0 0 0 0 0 0 0 0
        SEQUENCE: 0 0 0 0 0 0 0 0
    GET_LEASE_TIME: 0 0 0 0 0 0 0 0
    RECLAIM_COMPLETE: 0 0 0 0 0 0 0 0
       LAYOUTGET: 0 0 0 0 0 0 0 0
    GETDEVICEINFO: 0 0 0 0 0 0 0 0
    LAYOUTCOMMIT: 0 0 0 0 0 0 0 0
"""
        print pretty_print(parser.parse(input))

def pretty_print(str):
    #parsed = json.loads(str)
    return json.dumps(str, indent=4, sort_keys=True)

def print_usage():
    print "Syntax: %s [example_name]" % sys.argv[0]
    print "  example_name is one of %s" % schemas

if __name__ == '__main__':
    schemas=["pbs.accouting.log","pbs.server.log","pbs.mom.log","xfs.quota.report","nfs.mountstats"]
    if len(sys.argv)<2:
        print_usage()
        sys.exit(1)
    example=sys.argv[1]
    if not example in schemas:
        print_usage()
        sys.exit(1)
    presenter = ExamplePresenter()
    func = getattr(presenter,'show_%s'%example.replace('.','_'))
    func()
