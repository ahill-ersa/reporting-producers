#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.plugins.pbs import AccountingLogParser, ServerLogParser, MomLogParser
from reporting.plugins.xfs import QuotaReportParser
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


def pretty_print(str):
    #parsed = json.loads(str)
    return json.dumps(str, indent=4, sort_keys=True)

def print_usage():
    print "Syntax: %s [example_name]" % sys.argv[0]
    print "  example_name is one of %s" % schemas

if __name__ == '__main__':
    schemas=["pbs.accouting.log","pbs.server.log","pbs.mom.log","xfs.quota.report"]
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
