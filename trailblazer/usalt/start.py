# -*- coding: utf-8 -*-
import logging
import signal
import subprocess

from trailblazer.exc import MipStartError

LOG = logging.getLogger(__name__)

class UsaltCli(object):

    """Wrapper around MIP command line interface."""

    def __init__(self, script):
        self.script = script
  
    def __call__(self, config, family, **kwargs):
        """Execute the pipeline."""
        import pdb; pdb.set_trace()
        command = self.build_command(family=family, **kwargs)
        LOG.debug(' '.join(command))
        process = self.execute(command)
        process.wait()
        if process.returncode != 0:
            raise MipStartError('error starting analysis, check the output')
        return process

    def build_command(self, family, **kwargs):
        """Builds the command to execute uSALT."""
        cmd = "{} start project {}".format(self.script, family)
        cmd = cmd.split(' ')
        for key, value in kwargs.items():
            #Unary and binary arguments
            if value is True:
                cmd.append("--{}".format(value))
            else:
                cmd.append("--{}".format(key))
                cmd.append(value) 
        return cmd

    def execute(self, command):
        """Start a uSALT run."""
        process = subprocess.Popen(
            command,
            preexec_fn=lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        )
        return process
