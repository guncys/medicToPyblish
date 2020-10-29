# -*- coding: utf-8 -*-

name = 'medicToPyblish'

version = '1.0.0'

requires = ['maya', 'medic', 'pyblish']

build_command = "python -m rezutil build {root}"
private_build_requires = ['rezutil-1']

def commands():
    global env
    
    env.PYTHONPATH.append("{root}/python")
    env.PYTHONPATH.append("{root}/startup")
