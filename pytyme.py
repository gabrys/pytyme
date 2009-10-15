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
    
class NoCurrentTask(Exception):
    pass

make_pytyme_dirs()

if sys.argv[1] == 'start':
    project_name, task_name = sys.argv[2].split('/', 1)
    Project(project_name).task(task_name).start()

if sys.argv[1] == 'stop':
    current_task().stop()

