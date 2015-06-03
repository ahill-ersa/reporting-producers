#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.plugins.pbs import AccountingLogParser, ServerLogParser, MomLogParser
from reporting.plugins.xfs import QuotaReportParser, StatParser
from reporting.plugins.nfs import MountstatsParser
from reporting.parsers import JsonGrepParser, SplitParser
from reporting.plugins.mysql import ProcParser, StatusParser
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
    def show_xfs_stat(object):
        parser=StatParser()
        input= \
"""extent_alloc 19878117 1773698647 19897647 1287000233
abt 0 0 0 0
blk_map 2512303056 1635689861 27057563 19874604 24013769 4175062167 0
bmbt 0 0 0 0
dir 143718277 36812005 36545192 2172451094
trans 179275 268819079 4828871
ig 0 118304735 1112 19285303 0 16488585 7012513
log 30824769 544571813 0 32210012 29083063
push_ail 309844230 0 972087645 75698180 0 6769476 72631 4901168 0 1154810
xstrat 19861979 0
rw 272182346 2833486703
attr 1475275437 4730856 5519922 69483525
icluster 41912057 3429775 3879802
vnodes 4256084965 0 0 0 38882331 38882331 38882331 0
buf 815377194 3683521 811791503 14969 195162 3585691 0 7220386 3559508
abtb2 40554932 510658393 9925830 9886271 0 0 198942 18321 4703 17157 1273 1178 1273 1178 205077859
abtc2 83255623 1001261335 31732739 31693167 0 0 31259 1510 7916 26763 659 551 659 551 1380855943
bmbt2 58748 463899 22263 5784 0 0 0 0 0 0 0 0 0 0 0
ibt2 114391904 1116413643 1701 451 0 0 45874495 210074 0 227 1 0 1 0 341875
qm 0 0 0 0 0 0 0 0
xpc 7254653816832 8583095183622 95931284121085
debug 0"""
        print pretty_print(parser.parse(input))
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
    def show_hcp_chargeback(object):
        parser=JsonGrepParser(pattern="chargebackData", list_name="hcp-chargeback")
        input= \
"""
{"chargebackData":[{"systemName":"hcp1.s3.ersa.edu.au","valid":false,"bytesOut":286733200362,"deletes":689,"bytesIn":408536396027,"reads":1315,"writes":1707,"namespaceName":"modc08","tenantName":"dev","storageCapacityUsed":8381468672,"ingestedVolume":8380552280,"startTime":"2014-12-04T13:03:34+1030","endTime":"2015-05-13T17:06:51+0930","deleted":"false","objectCount":480},{"systemName":"hcp1.s3.ersa.edu.au","valid":false,"bytesOut":240726068,"deletes":49,"bytesIn":233496746,"reads":3197,"writes":159,"namespaceName":"unisatest","tenantName":"dev","storageCapacityUsed":258048,"ingestedVolume":227573,"startTime":"2015-04-17T12:53:51+0930","endTime":"2015-05-13T17:06:51+0930","deleted":"false","objectCount":11},{"systemName":"hcp1.s3.ersa.edu.au","valid":false,"bytesOut":286973926430,"deletes":738,"bytesIn":408769892773,"reads":4512,"writes":1866,"tenantName":"dev","storageCapacityUsed":8381726720,"ingestedVolume":8380779853,"startTime":"2014-12-04T12:13:08+1030","endTime":"2015-05-13T17:06:51+0930","deleted":"false","objectCount":491}]}
"""    
#["chargebackData1","chargebackData2"]
#[{"chargebackData": 1}, {"chargebackData": 2}]
        print pretty_print(parser.parse(input))
    def show_mysql_stat(object):
        input="Uptime: 15312260  Threads: 75  Questions: 1437448576  Slow queries: 0  Opens: 330  Flush tables: 1  Open tables: 239  Queries per second avg: 93.875"
        parser=SplitParser("\s+", "{{\"Uptime\":{1},\"Threads\":{3},\"Questions\":{5},\"Slow queries\":{8},\"Opens\":{10},\"Flush tables\":{13},\"Open tables\":{16},\"Queries per second avg\":{21}}}")
        print pretty_print(parser.parse(input))
    def show_mysql_proc(object):
        input= \
"""+----------+-------------+--------------------------------------------+------+-------------+----------+-----------------------------------------------------------------------------+------------------+
| Id       | User        | Host                                       | db   | Command     | Time     | State                                                                       | Info             |
+----------+-------------+--------------------------------------------+------+-------------+----------+-----------------------------------------------------------------------------+------------------+
| 1        | system user |                                            |      | Connect     | 15315680 | Waiting for master to send event                                            |                  |
| 2        | system user |                                            |      | Connect     | 9072222  | Slave has read all relay log; waiting for the slave I/O thread to update it |                  |
| 191      | backup      | cw-mysql-02-private.sa.nectar.org.au:38912 |      | Binlog Dump | 15315391 | Master has sent all binlog to slave; waiting for binlog to be updated       |                  |
| 32981036 | nova        | 192.168.16.230:41317                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981038 | nova        | 192.168.16.230:41320                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981039 | nova        | 192.168.16.230:41321                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981042 | nova        | 192.168.16.230:41326                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981043 | nova        | 192.168.16.230:41328                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981045 | nova        | 192.168.16.230:41331                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981050 | nova        | 192.168.16.230:41337                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981051 | nova        | 192.168.16.230:41339                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981055 | nova        | 192.168.16.230:41344                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981056 | nova        | 192.168.16.230:41347                       | nova | Sleep       | 11       |                                                                             |                  |
| 32981059 | nova        | 192.168.16.230:41353                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981062 | nova        | 192.168.16.230:41358                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981065 | nova        | 192.168.16.230:41363                       | nova | Sleep       | 9        |                                                                             |                  |
| 32981070 | nova        | 192.168.16.230:41369                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981071 | nova        | 192.168.16.230:41371                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981072 | nova        | 192.168.16.230:41372                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981075 | nova        | 192.168.16.230:41377                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981077 | nova        | 192.168.16.230:41380                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981079 | nova        | 192.168.16.230:41382                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981082 | nova        | 192.168.16.230:41388                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981083 | nova        | 192.168.16.230:41390                       | nova | Sleep       | 3        |                                                                             |                  |
| 32981085 | nova        | 192.168.16.230:41392                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981086 | nova        | 192.168.16.230:41394                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981087 | nova        | 192.168.16.230:41395                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981089 | nova        | 192.168.16.230:41397                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981090 | nova        | 192.168.16.230:41398                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981097 | nova        | 192.168.16.230:41408                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981098 | nova        | 192.168.16.230:41409                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981100 | nova        | 192.168.16.230:41413                       | nova | Sleep       | 3        |                                                                             |                  |
| 32981101 | nova        | 192.168.16.230:41415                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981102 | nova        | 192.168.16.230:41416                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981104 | nova        | 192.168.16.230:41417                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981105 | nova        | 192.168.16.230:41418                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981106 | nova        | 192.168.16.230:41420                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981108 | nova        | 192.168.16.230:41424                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981109 | nova        | 192.168.16.230:41425                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981111 | nova        | 192.168.16.230:41427                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981112 | nova        | 192.168.16.230:41428                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981115 | nova        | 192.168.16.230:41432                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981119 | nova        | 192.168.16.230:41439                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981120 | nova        | 192.168.16.230:41440                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981122 | nova        | 192.168.16.230:41441                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981123 | nova        | 192.168.16.230:41443                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981125 | nova        | 192.168.16.230:41447                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981126 | nova        | 192.168.16.230:41448                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981130 | nova        | 192.168.16.230:41455                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981131 | nova        | 192.168.16.230:41456                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981132 | nova        | 192.168.16.230:41458                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981135 | nova        | 192.168.16.230:41462                       | nova | Sleep       | 3        |                                                                             |                  |
| 32981137 | nova        | 192.168.16.230:41465                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981138 | nova        | 192.168.16.230:41467                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981140 | nova        | 192.168.16.230:41469                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981141 | nova        | 192.168.16.230:41470                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981145 | nova        | 192.168.16.230:41476                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981146 | nova        | 192.168.16.230:41477                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981147 | nova        | 192.168.16.230:41478                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981148 | nova        | 192.168.16.230:41479                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981151 | nova        | 192.168.16.230:41484                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981153 | nova        | 192.168.16.230:41486                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981154 | nova        | 192.168.16.230:41487                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981156 | nova        | 192.168.16.230:41491                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981157 | nova        | 192.168.16.230:41492                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981161 | nova        | 192.168.16.230:41498                       | nova | Sleep       | 8        |                                                                             |                  |
| 32981164 | nova        | 192.168.16.230:41502                       | nova | Sleep       | 2        |                                                                             |                  |
| 32981169 | nova        | 192.168.16.230:41509                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981170 | nova        | 192.168.16.230:41511                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981171 | nova        | 192.168.16.230:41512                       | nova | Sleep       | 5        |                                                                             |                  |
| 32981172 | nova        | 192.168.16.230:41513                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981174 | nova        | 192.168.16.230:41515                       | nova | Sleep       | 0        |                                                                             |                  |
| 32981176 | nova        | 192.168.16.230:41520                       | nova | Sleep       | 3        |                                                                             |                  |
| 32981179 | nova        | 192.168.16.230:41525                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981180 | nova        | 192.168.16.230:41526                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981181 | nova        | 192.168.16.230:41527                       | nova | Sleep       | 1        |                                                                             |                  |
| 32981183 | root        | localhost                                  |      | Query       | 0        |                                                                             | show processlist |
+----------+-------------+--------------------------------------------+------+-------------+----------+-----------------------------------------------------------------------------+------------------+
"""
        parser=ProcParser()
        print pretty_print(parser.parse(input))
    def show_mysql_status(object):
        input= \
"""+------------------------------------------+----------------+
| Variable_name                            | Value          |
+------------------------------------------+----------------+
| Aborted_clients                          | 594455         |
| Aborted_connects                         | 227            |
| Binlog_cache_disk_use                    | 0              |
| Binlog_cache_use                         | 187605037      |
| Binlog_stmt_cache_disk_use               | 0              |
| Binlog_stmt_cache_use                    | 1588330        |
| Bytes_received                           | 666616367255   |
| Bytes_sent                               | 3834519411100  |
| Com_admin_commands                       | 19             |
| Com_assign_to_keycache                   | 0              |
| Com_alter_db                             | 0              |
| Com_alter_db_upgrade                     | 0              |
| Com_alter_event                          | 0              |
| Com_alter_function                       | 0              |
| Com_alter_procedure                      | 0              |
| Com_alter_server                         | 0              |
| Com_alter_table                          | 22             |
| Com_alter_tablespace                     | 0              |
| Com_analyze                              | 0              |
| Com_begin                                | 49             |
| Com_binlog                               | 0              |
| Com_call_procedure                       | 0              |
| Com_change_db                            | 8              |
| Com_change_master                        | 0              |
| Com_check                                | 0              |
| Com_checksum                             | 0              |
| Com_commit                               | 208590740      |
| Com_create_db                            | 0              |
| Com_create_event                         | 0              |
| Com_create_function                      | 0              |
| Com_create_index                         | 3              |
| Com_create_procedure                     | 0              |
| Com_create_server                        | 0              |
| Com_create_table                         | 2              |
| Com_create_trigger                       | 0              |
| Com_create_udf                           | 0              |
| Com_create_user                          | 9              |
| Com_create_view                          | 0              |
| Com_dealloc_sql                          | 0              |
| Com_delete                               | 4294592        |
| Com_delete_multi                         | 0              |
| Com_do                                   | 0              |
| Com_drop_db                              | 0              |
| Com_drop_event                           | 0              |
| Com_drop_function                        | 0              |
| Com_drop_index                           | 1              |
| Com_drop_procedure                       | 0              |
| Com_drop_server                          | 0              |
| Com_drop_table                           | 2              |
| Com_drop_trigger                         | 0              |
| Com_drop_user                            | 10             |
| Com_drop_view                            | 0              |
| Com_empty_query                          | 0              |
| Com_execute_sql                          | 0              |
| Com_flush                                | 19             |
| Com_grant                                | 5              |
| Com_ha_close                             | 0              |
| Com_ha_open                              | 0              |
| Com_ha_read                              | 0              |
| Com_help                                 | 1              |
| Com_insert                               | 551903         |
| Com_insert_select                        | 0              |
| Com_install_plugin                       | 0              |
| Com_kill                                 | 4              |
| Com_load                                 | 0              |
| Com_lock_tables                          | 0              |
| Com_optimize                             | 0              |
| Com_preload_keys                         | 0              |
| Com_prepare_sql                          | 0              |
| Com_purge                                | 0              |
| Com_purge_before_date                    | 0              |
| Com_release_savepoint                    | 0              |
| Com_rename_table                         | 0              |
| Com_rename_user                          | 0              |
| Com_repair                               | 0              |
| Com_replace                              | 0              |
| Com_replace_select                       | 0              |
| Com_reset                                | 0              |
| Com_resignal                             | 0              |
| Com_revoke                               | 0              |
| Com_revoke_all                           | 0              |
| Com_rollback                             | 342142336      |
| Com_rollback_to_savepoint                | 0              |
| Com_savepoint                            | 0              |
| Com_select                               | 645108339      |
| Com_set_option                           | 20065179       |
| Com_signal                               | 0              |
| Com_show_authors                         | 0              |
| Com_show_binlog_events                   | 0              |
| Com_show_binlogs                         | 0              |
| Com_show_charsets                        | 0              |
| Com_show_collations                      | 493            |
| Com_show_contributors                    | 0              |
| Com_show_create_db                       | 51006          |
| Com_show_create_event                    | 0              |
| Com_show_create_func                     | 0              |
| Com_show_create_proc                     | 0              |
| Com_show_create_table                    | 44             |
| Com_show_create_trigger                  | 0              |
| Com_show_databases                       | 51036          |
| Com_show_engine_logs                     | 0              |
| Com_show_engine_mutex                    | 0              |
| Com_show_engine_status                   | 1              |
| Com_show_events                          | 0              |
| Com_show_errors                          | 0              |
| Com_show_fields                          | 19468          |
| Com_show_function_status                 | 0              |
| Com_show_grants                          | 0              |
| Com_show_keys                            | 0              |
| Com_show_master_status                   | 12             |
| Com_show_open_tables                     | 0              |
| Com_show_plugins                         | 0              |
| Com_show_privileges                      | 0              |
| Com_show_procedure_status                | 0              |
| Com_show_processlist                     | 7              |
| Com_show_profile                         | 0              |
| Com_show_profiles                        | 0              |
| Com_show_relaylog_events                 | 0              |
| Com_show_slave_hosts                     | 0              |
| Com_show_slave_status                    | 12             |
| Com_show_status                          | 59412          |
| Com_show_storage_engines                 | 0              |
| Com_show_table_status                    | 1              |
| Com_show_tables                          | 37             |
| Com_show_triggers                        | 0              |
| Com_show_variables                       | 6834           |
| Com_show_warnings                        | 0              |
| Com_slave_start                          | 0              |
| Com_slave_stop                           | 0              |
| Com_stmt_close                           | 0              |
| Com_stmt_execute                         | 0              |
| Com_stmt_fetch                           | 0              |
| Com_stmt_prepare                         | 0              |
| Com_stmt_reprepare                       | 0              |
| Com_stmt_reset                           | 0              |
| Com_stmt_send_long_data                  | 0              |
| Com_truncate                             | 0              |
| Com_uninstall_plugin                     | 0              |
| Com_unlock_tables                        | 0              |
| Com_update                               | 184534310      |
| Com_update_multi                         | 0              |
| Com_xa_commit                            | 0              |
| Com_xa_end                               | 0              |
| Com_xa_prepare                           | 0              |
| Com_xa_recover                           | 0              |
| Com_xa_rollback                          | 0              |
| Com_xa_start                             | 0              |
| Compression                              | OFF            |
| Connections                              | 32982869       |
| Created_tmp_disk_tables                  | 18052667       |
| Created_tmp_files                        | 155            |
| Created_tmp_tables                       | 37306175       |
| Delayed_errors                           | 0              |
| Delayed_insert_threads                   | 0              |
| Delayed_writes                           | 0              |
| Flush_commands                           | 1              |
| Handler_commit                           | 1107325090     |
| Handler_delete                           | 204            |
| Handler_discover                         | 0              |
| Handler_prepare                          | 739440150      |
| Handler_read_first                       | 57219026       |
| Handler_read_key                         | 1079191624     |
| Handler_read_last                        | 0              |
| Handler_read_next                        | 75094236269    |
| Handler_read_prev                        | 0              |
| Handler_read_rnd                         | 36495030       |
| Handler_read_rnd_next                    | 40252048035    |
| Handler_rollback                         | 130018224      |
| Handler_savepoint                        | 0              |
| Handler_savepoint_rollback               | 0              |
| Handler_update                           | 184493182      |
| Handler_write                            | 160590072      |
| Innodb_buffer_pool_pages_data            | 8085           |
| Innodb_buffer_pool_bytes_data            | 132464640      |
| Innodb_buffer_pool_pages_dirty           | 307            |
| Innodb_buffer_pool_bytes_dirty           | 5029888        |
| Innodb_buffer_pool_pages_flushed         | 88174850       |
| Innodb_buffer_pool_pages_free            | 0              |
| Innodb_buffer_pool_pages_misc            | 106            |
| Innodb_buffer_pool_pages_total           | 8191           |
| Innodb_buffer_pool_read_ahead_rnd        | 0              |
| Innodb_buffer_pool_read_ahead            | 342974591      |
| Innodb_buffer_pool_read_ahead_evicted    | 22360646       |
| Innodb_buffer_pool_read_requests         | 245423976935   |
| Innodb_buffer_pool_reads                 | 1218202021     |
| Innodb_buffer_pool_wait_free             | 0              |
| Innodb_buffer_pool_write_requests        | 1370397998     |
| Innodb_data_fsyncs                       | 372682814      |
| Innodb_data_pending_fsyncs               | 0              |
| Innodb_data_pending_reads                | 0              |
| Innodb_data_pending_writes               | 0              |
| Innodb_data_read                         | 25579709091840 |
| Innodb_data_reads                        | 1234555928     |
| Innodb_data_writes                       | 408660492      |
| Innodb_data_written                      | 3165477558784  |
| Innodb_dblwr_pages_written               | 88174850       |
| Innodb_dblwr_writes                      | 2069085        |
| Innodb_have_atomic_builtins              | ON             |
| Innodb_log_waits                         | 0              |
| Innodb_log_write_requests                | 172944312      |
| Innodb_log_writes                        | 367047033      |
| Innodb_os_log_fsyncs                     | 368562229      |
| Innodb_os_log_pending_fsyncs             | 0              |
| Innodb_os_log_pending_writes             | 0              |
| Innodb_os_log_written                    | 275388476928   |
| Innodb_page_size                         | 16384          |
| Innodb_pages_created                     | 3440620        |
| Innodb_pages_read                        | 1561261436     |
| Innodb_pages_written                     | 88174850       |
| Innodb_row_lock_current_waits            | 0              |
| Innodb_row_lock_time                     | 6977           |
| Innodb_row_lock_time_avg                 | 1              |
| Innodb_row_lock_time_max                 | 36             |
| Innodb_row_lock_waits                    | 5093           |
| Innodb_rows_deleted                      | 16             |
| Innodb_rows_inserted                     | 532233         |
| Innodb_rows_read                         | 113987397310   |
| Innodb_rows_updated                      | 184487786      |
| Innodb_truncated_status_writes           | 0              |
| Key_blocks_not_flushed                   | 0              |
| Key_blocks_unused                        | 0              |
| Key_blocks_used                          | 13396          |
| Key_read_requests                        | 44714498       |
| Key_reads                                | 1668221        |
| Key_write_requests                       | 214742         |
| Key_writes                               | 208884         |
| Last_query_cost                          | 0.000000       |
| Max_used_connections                     | 180            |
| Not_flushed_delayed_rows                 | 0              |
| Open_files                               | 58             |
| Open_streams                             | 0              |
| Open_table_definitions                   | 156            |
| Open_tables                              | 239            |
| Opened_files                             | 72219700       |
| Opened_table_definitions                 | 230            |
| Opened_tables                            | 330            |
| Performance_schema_cond_classes_lost     | 0              |
| Performance_schema_cond_instances_lost   | 0              |
| Performance_schema_file_classes_lost     | 0              |
| Performance_schema_file_handles_lost     | 0              |
| Performance_schema_file_instances_lost   | 0              |
| Performance_schema_locker_lost           | 0              |
| Performance_schema_mutex_classes_lost    | 0              |
| Performance_schema_mutex_instances_lost  | 0              |
| Performance_schema_rwlock_classes_lost   | 0              |
| Performance_schema_rwlock_instances_lost | 0              |
| Performance_schema_table_handles_lost    | 0              |
| Performance_schema_table_instances_lost  | 0              |
| Performance_schema_thread_classes_lost   | 0              |
| Performance_schema_thread_instances_lost | 0              |
| Prepared_stmt_count                      | 0              |
| Qcache_free_blocks                       | 142            |
| Qcache_free_memory                       | 659272         |
| Qcache_hits                              | 26877          |
| Qcache_inserts                           | 260387619      |
| Qcache_lowmem_prunes                     | 46027454       |
| Qcache_not_cached                        | 385178880      |
| Qcache_queries_in_cache                  | 897            |
| Qcache_total_blocks                      | 2887           |
| Queries                                  | 1437831472     |
| Questions                                | 1437831336     |
| Rpl_status                               | AUTH_MASTER    |
| Select_full_join                         | 5066           |
| Select_full_range_join                   | 0              |
| Select_range                             | 3209501        |
| Select_range_check                       | 0              |
| Select_scan                              | 20112233       |
| Slave_heartbeat_period                   | 1800.000       |
| Slave_open_temp_tables                   | 0              |
| Slave_received_heartbeats                | 9              |
| Slave_retried_transactions               | 0              |
| Slave_running                            | ON             |
| Slow_launch_threads                      | 0              |
| Slow_queries                             | 0              |
| Sort_merge_passes                        | 72             |
| Sort_range                               | 31285046       |
| Sort_rows                                | 28906895       |
| Sort_scan                                | 687208         |
| Ssl_accept_renegotiates                  | 0              |
| Ssl_accepts                              | 0              |
| Ssl_callback_cache_hits                  | 0              |
| Ssl_cipher                               |                |
| Ssl_cipher_list                          |                |
| Ssl_client_connects                      | 0              |
| Ssl_connect_renegotiates                 | 0              |
| Ssl_ctx_verify_depth                     | 0              |
| Ssl_ctx_verify_mode                      | 0              |
| Ssl_default_timeout                      | 0              |
| Ssl_finished_accepts                     | 0              |
| Ssl_finished_connects                    | 0              |
| Ssl_session_cache_hits                   | 0              |
| Ssl_session_cache_misses                 | 0              |
| Ssl_session_cache_mode                   | NONE           |
| Ssl_session_cache_overflows              | 0              |
| Ssl_session_cache_size                   | 0              |
| Ssl_session_cache_timeouts               | 0              |
| Ssl_sessions_reused                      | 0              |
| Ssl_used_session_cache_entries           | 0              |
| Ssl_verify_depth                         | 0              |
| Ssl_verify_mode                          | 0              |
| Ssl_version                              |                |
| Table_locks_immediate                    | 724714292      |
| Table_locks_waited                       | 1              |
| Tc_log_max_pages_used                    | 0              |
| Tc_log_page_size                         | 0              |
| Tc_log_page_waits                        | 13             |
| Threads_cached                           | 4              |
| Threads_connected                        | 75             |
| Threads_created                          | 175156         |
| Threads_running                          | 2              |
| Uptime                                   | 15316374       |
| Uptime_since_flush_status                | 15316374       |
+------------------------------------------+----------------+
"""
        parser=StatusParser()
        print pretty_print(parser.parse(input))
    
def pretty_print(str):
    #parsed = json.loads(str)
    return json.dumps(str, indent=4, sort_keys=True)

def print_usage():
    print "Syntax: %s [example_name]" % sys.argv[0]
    print "  example_name is one of %s" % schemas

if __name__ == '__main__':
    schemas=["pbs.accouting.log","pbs.server.log","pbs.mom.log","xfs.quota.report","xfs.stat","nfs.mountstats","hcp.chargeback","mysql.stat","mysql.proc","mysql.status"]
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
