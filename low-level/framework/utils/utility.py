"""
Base class for all the Utility implementation
"""

import subprocess

try:
    from service_logging import logger
except Exception as e:
    from framework.utils.service_logging import logger

class Utility(object):
    """Base class for all the utilities
    """
    def __init__(self):
        """Init method"""
        super(Utility, self).__init__()

    def execute_cmd(self, command=[]):
        """Executes action using python subprocess module
           and returns the output
           1. output of the command in byte
           2. return_code).
        """
        #TODO Handle exception at caller side
        process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE,\
                                    stderr=subprocess.PIPE)
        return process.communicate()[0], process.returncode

    def is_env_vm(self):
        """
        Returns true if VM env, false otherwise
        """
        is_vm = True
        CMD = "facter is_virtual"
        try:
            subout = subprocess.Popen(CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = subout.stdout.readlines()
            if result == [] or result == "":
                logger.warning("Not able to read whether env is vm or not, assuming VM env.")
            else:
                if 'false' in result[0].decode():
                    is_vm = False
        except Exception as e:
            logger.warning("Error while reading whether env is vm or not, assuming VM env : {e}")
        return is_vm
