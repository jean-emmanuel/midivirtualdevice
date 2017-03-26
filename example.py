#encoding: utf-8

from pyo import *

from midivirtualdevice import MidiVirtualDevice

from time import sleep

virtual = MidiVirtualDevice(['test'])

def midicall(*args):
    print(args)

listen = MidiListener(midicall, virtual.ports['test']['in'])

dispatch = MidiDispatcher(virtual.ports['test']['out'])

listen.start()
dispatch.start()

print('MidiVirtualDevice is running (ctr+c to stop)')

try:
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
