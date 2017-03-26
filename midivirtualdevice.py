#encoding: utf-8

from pyo import pm_get_input_devices, pm_get_output_devices
from threading import Thread
from signal import signal, SIGINT, SIGTERM

import mididings

class MidiVirtualDevice(object):
    """
    Virtual ALSA MIDI Device for pyo.
    """

    def __init__(self, ports, name='Pyo Virtal MIDI'):
        """
        MidiVirtualDevice constructor

        Args:

            ports (str|list): port's name or list of ports to open
            name      (name): device's name (for ALSA)


        This will create a virtual midi device with the following ports:
        (where PORT is the port's name)

        Inputs:

            _pyo_out_PORT : pyo's midi output (don't connect it with ALSA/Jack)
            PORT_in       : ALSA midi input (internally routed to _pyo_in_PORT)

        Outputs:

            _pyo_in_PORT : pyo's midi input (don't connect it with ALSA/Jack)
            PORT_out     : ALSA midi output (internally routed to _pyo_out_PORT)


        There's no error here: ALSA's midi inputs are outputs for pyo/portmidi
                               and vice-versa

        Usage:

            from pyo import *
            from midivirtualdevice import MidiVirtualDevice

            virtual = MidiVirtualDevice(['test'])

            listen = MidiListener(midicall, virtual.ports['test']['in'])
            dispatch = MidiDispatcher(virtual.ports['test']['out'])


        """


        # Singleton check (can't run multiple mididings engines in the same process)
        if mididings.engine.active():
            print('Error: can\'t open multiple virtual midi devices in the same process (ports=%s, name=%s)' % (ports, name))
            return None


        self.ports = {}

        if type(ports) is not list:
            ports = [ports]

        self._alsa_in_ports = []
        self._alsa_out_ports = []

        for port in ports:

            self.ports[port] = {}

            self._alsa_in_ports.insert(0,'_pyo_%s_out' % port)
            self._alsa_out_ports.insert(0,'_pyo_%s_in' % port)

            self._alsa_in_ports.append('%s_in' % port)
            self._alsa_out_ports.append('%s_out' % port)


        # set mididings config

        mididings.config(
            backend='alsa',
            client_name=name,
            in_ports=self._alsa_in_ports,
            out_ports=self._alsa_out_ports
        )


        # construct mididings midi routing patch

        self.patch = []

        for port in self.ports:
            self.patch.append(
                mididings.PortFilter('_pyo_%s_out' % port) >> mididings.Port('%s_out' % port),
            )
            self.patch.append(
                mididings.PortFilter('%s_in' % port) >> mididings.Port('_pyo_%s_in' % port)
            )

        # start mididings engine

        thread = Thread(target=mididings.run, args=[self.patch])
        thread.daemon = True
        thread.start()


        # get virtual device ports ids as seen by port midi
        # and store them in self.ports

        pm_input_devices = pm_get_input_devices()
        pm_output_devices = pm_get_output_devices()

        for port in self.ports:

            x = -1
            for name in pm_input_devices[0]:
                x += 1
                if name == '_pyo_%s_in' % port:
                    self.ports[port]['in'] = pm_input_devices[1][x]

            x = -1
            for name in pm_output_devices[0]:
                x += 1
                if name == '_pyo_%s_out' % port:
                    self.ports[port]['out'] = pm_output_devices[1][x]

    def stop(self, *args):
        if mididings.engine.active():
            mididings.engine.quit()
