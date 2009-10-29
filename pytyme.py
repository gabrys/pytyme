#!/usr/bin/env python

import sys
import os
import time
import datetime

PYTYME_DIR = os.path.join(os.path.expanduser('~'), '.pytyme')
CURRENT_TASK_PATH = os.path.join(PYTYME_DIR, 'current_task')
PROJECTS_DIR = os.path.join(PYTYME_DIR, 'projects')
NOW = long(time.time() * 1000)
DEFAULT_PERIOD_COMMENT = datetime.datetime.now().strftime('%B %Y')

def mkdir_p(dir):
    try:
        os.makedirs(dir)
    except OSError, e:
        pass


def make_pytyme_dirs():
    mkdir_p(PROJECTS_DIR)

def current_task():
    try:
        project_name, period_name, task_name = open(CURRENT_TASK_PATH, 'r').read().split('/')
    except IOError:
        raise NoCurrentTask()
    return Project(project_name).period(period_name).task(task_name)

def set_current_task(task):
    open(CURRENT_TASK_PATH, 'w').write(task.project.name + '/' + task.period.name + '/' + task.name)

def del_current_task():
    os.remove(CURRENT_TASK_PATH)

def time_pretty(total):
    seconds = int(total)
    minutes = seconds / 60
    seconds = seconds % 60
    hours = minutes / 60
    minutes = minutes % 60
    
    parts = []
    if hours > 0:
        parts.append(str(hours) + "h")
    if minutes > 0:
        parts.append(str(minutes) + "m")
    
    s = " ".join(parts)
    if s == "":
        return '0m'
    else:
        return s

class Project(object):
    def __init__(self, name):
        self.name = name
        self.dir = os.path.join(PROJECTS_DIR, self.name)
        mkdir_p(self.dir)

    def current_period(self):
        periods = []
        dirs = [file for file in os.listdir(self.dir) if file[0] != '.' and os.path.isdir(os.path.join(self.dir, file))]
        for dir in dirs:
            try:
                time = long(dir.split(',')[0])
                periods.append((time, dir))
            except Exception, e:
                pass
        try:
            return Period(self, sorted(periods)[-1][1])
        except IndexError:
            return Period.create(self)

    def period(self, name):
        return Period(self, name)

    def task(self, name):
        return self.current_period().task(name)

    @classmethod
    def all(cls):
        for dir in [file for file in os.listdir(PROJECTS_DIR) if file[0] != '.' and os.path.isdir(os.path.join(PROJECTS_DIR, file))]:
            yield Project(dir)


class Period(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name
        self.dir = os.path.join(self.project.dir, name)
        mkdir_p(self.dir)

    @classmethod
    def create(cls, project, comment=DEFAULT_PERIOD_COMMENT):
        name = str(NOW) + ',' + comment
        return cls(project, name)

    def task(self, name):
        return Task(self, name)

    def tasks(self):
        for dir in [file for file in os.listdir(self.dir) if file[0] != '.' and os.path.isfile(os.path.join(self.dir, file))]:
            yield Task(self, dir)

    def is_active(self):
        for task in self.tasks():
            return True
        return False

    def total_time(self):
        total = 0
        for task in self.tasks():
            total += task.total_time()
        return total

    def pretty_print(self):
        return "Project: %s\nPeriod: %s\nTotal time: %s\n\n  %s" % (
            self.project.name,
            self.name.split(',')[1],
            time_pretty(self.total_time()),
            "\n\n  ".join([task.pretty_print().replace("\n", "\n  ") for task in self.tasks()])
        )


class Task(object):
    def __init__(self, period, name):
        self.period = period
        self.project = period.project
        self.name = name
        self.filename = os.path.join(self.period.dir, name)
        self.file = file(self.filename, 'a')

    def start(self, when=NOW):
        try:
            current_task().stop()
        except NoCurrentTask:
            pass
        if when == None:
            when = NOW
        set_current_task(self)
        self.file.write(str(when) + ',')

    def stop(self, when=NOW, comment=''):
        del_current_task()
        self.file.write(str(when) + ',' + comment + '\n')

    def times(self):
        try:
            return self._times
        except:
            self._times = []
            filero = file(self.filename, 'r')
            for t in [line.split(',') for line in filero.read().split('\n')]:
                try:
                    r = {}
                    r['time1f'] = float(t[0]) / 1000
                    r['time1s'] = time.strftime('%Y-%m-%d %H:%M', time.gmtime(r['time1f']))
                    try:
                        r['time2f'] = float(t[1]) / 1000
                        r['time2s'] = time.strftime('%Y-%m-%d %H:%M', time.gmtime(r['time2f']))
                    except:
                        r['time2f'] = NOW / 1000
                        r['time2s'] = 'NOW'
                    try:
                        r['comment'] = t[2]
                    except:
                        r['comment'] = ''
                    r['total'] = r['time2f'] - r['time1f']
                    self._times.append(r)
                except:
                    pass
            return self._times

    def total_time(self):
        total = 0
        for time in self.times():
            total += time['total']
        return total

    def pretty_print(self):
        filero = file(self.filename, 'r')
        times = ["%s - %s  %s" % (time['time1s'], time['time2s'], time['comment']) for time in self.times()]
        return "Task: %s (total: %s)\n  %s" % (self.name, time_pretty(self.total_time()), "\n  ".join(times))

    
class NoCurrentTask(Exception):
    pass

make_pytyme_dirs()

if len(sys.argv) == 1:
    periods = []
    for project in Project.all():
        period = project.current_period()
        if period.is_active():
            periods.append(period)
    print "\n" + "\n\n========================\n\n".join([period.pretty_print() for period in periods]) + "\n"
    
elif sys.argv[1] == 'start':
    project_name, task_name = sys.argv[2].split('/', 1)
    Project(project_name).task(task_name).start()

elif sys.argv[1] == 'stop':
    current_task().stop()

