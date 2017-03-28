#encoding: utf-8

from pyo import *
from midivirtualdevice import MidiVirtualDevice
from time import sleep

# Create a virtual midi device with one set of i/o named test

virtual = MidiVirtualDevice(['test'])


# Listen on virtual.ports['test']['out'] and print received midi

def midicall(*args):
    print(args)

listen = MidiListener(midicall, virtual.ports['test']['in'])
listen.start()

# Send a NoteOn/Off every second on virtual.ports['test']['out']

dispatch = MidiDispatcher(virtual.ports['test']['out'])
dispatch.start()

try:
    print('MidiVirtualDevice is running (ctr+c to stop)')
    while True:
        dispatch.send(144, 64, 64)
        dispatch.send(128, 64, 64)
        sleep(1)
except:
    # this is just for avoiding the error on exit
    pass


# plug some midi source to test_in with qjackcctl
# monitor test_out with qmidiroute
# yay !

virtual.stop()
