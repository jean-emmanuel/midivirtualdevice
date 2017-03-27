#encoding: utf-8

from pyo import pm_get_input_devices, pm_get_output_devices
from threading import Thread

import mididings

class MidiVirtualDevice(object):
    """
    Virtual ALSA MIDI Device for pyo.

    - ports prefixed with PM_PREFIX must not be connected via ALSA (pyo only)
    - ports prefixed with ALSA_PREFIX must not be connected via pyo (ALSA only)

    """

    PM_PREFIX = 'PYO_'
    ALSA_PREFIX = ''

    def __init__(self, ports, name='Pyo Virtal MIDI'):
        """
        MidiVirtualDevice constructor

        Args:

            ports (str|list): port's name or list of ports to open
            name      (name): device's name (for ALSA)

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

        x = -1
        for port in ports:

            x += 1

            self.ports[port] = {}

            self._alsa_in_ports.insert(x,'%s%s' % (self.PM_PREFIX, port))
            self._alsa_out_ports.insert(x,'%s%s' % (self.PM_PREFIX, port))

            self._alsa_in_ports.append('%s%s_in' % (self.ALSA_PREFIX, port))
            self._alsa_out_ports.append('%s%s_out' % (self.ALSA_PREFIX, port))


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
                mididings.PortFilter('%s%s' % (self.PM_PREFIX, port)) >> mididings.Port('%s%s_out' % (self.ALSA_PREFIX, port)),
            )
            self.patch.append(
                mididings.PortFilter('%s%s_in' % (self.ALSA_PREFIX, port)) >> mididings.Port('%s%s' % (self.PM_PREFIX, port))
            )

        # start mididings engine
        # for now, we use deamon thread, simple but not very clean
        # (mididings doesn't quit properly sometimes)

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
                if name == '%s%s' % (self.PM_PREFIX, port):
                    self.ports[port]['in'] = pm_input_devices[1][x]

            x = -1
            for name in pm_output_devices[0]:
                x += 1
                if name == '%s%s' % (self.PM_PREFIX, port):
                    self.ports[port]['out'] = pm_output_devices[1][x]

    def stop(self, *args):
        if mididings.engine.active():
            mididings.engine.quit()
