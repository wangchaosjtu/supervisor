import threading
import time
import pycron
from supervisor.supervisorctl import Controller
from supervisor.options import ClientOptions
from supervisor import loggers

crontab = {}
PERIOD = 60

def register(schedule, cmd):
    job = [schedule, cmd]
    job_id =  id(job)
    crontab[job_id] = job
    return job_id
 
def unregister(job_ids):
    for job_id in job_ids:
        crontab.pop(job_id)

def timeslice(period, when):
    return int(when - (when % period))

class Cron(threading.Thread):
    def __init__(self, args, logger):
        self.logger = logger
        options = ClientOptions()
        options.realize(args, doc=__doc__)
        self.controller = Controller(options)
        self.last_tick = None
        threading.Thread.__init__(self)

    def run(self):
        self.logger.info('CRON: start')
        self.is_running = True
        while self.is_running:
            self.tick()
            time.sleep(1)
        self.logger.info('CRON: end')
    
    def stop(self):
        self.is_running = False

    def tick(self):
        now = time.time()
        this_tick = timeslice(PERIOD, now)
        if self.last_tick is None:
            # we just started up
            self.last_tick = timeslice(PERIOD, now)
        if this_tick != self.last_tick:
            self.last_tick = this_tick            
            for schedule, cmd in crontab.values():
                if pycron.is_now(schedule):
                    self.logger.info(f'CRON ({schedule}): {cmd}')
                    self.controller.onecmd(cmd)