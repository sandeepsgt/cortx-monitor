# Copyright (c) 2001-2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>. For any questions
# about this software or licensing, please email opensource@seagate.com or
# cortx-questions@seagate.com.


import json
import re

from cortx.utils.process import SimpleProcess
from dbus import Array, Interface, SystemBus


class Disk:

    def __init__(self, _id, path, device) -> None:
        """Initialize Disk class."""
        self.id = str(_id)
        self.path = str(path)
        self.device = str(device)

    def get_health(self):
        if self._is_local_drive():
            smartctl = "sudo smartctl"
        else:
            smartctl = "sudo smartctl -d scsi"
        # Get smart availability attributes
        cmd = f"{smartctl} -i {self.device}"
        response, _, _ = SimpleProcess(cmd).run()
        response = response.decode()
        health_data = {}
        if re.findall("SMART support is: Available - device has SMART capability", response):
            health_data["SMART_available"] = True
        else:
            health_data["SMART_available"] = False
        if re.findall("SMART support is: Enabled", response):
            health_data["SMART_support"] = "Enabled"
        else:
            health_data["SMART_support"] = "NA"
        # Get smart health attributes
        cmd = f"{smartctl} --all {self.device} --json"
        response, _, _ = SimpleProcess(cmd).run()
        response = json.loads(response)
        try:
            smart_test_status = "PASSED" if response['smart_status']['passed'] else "FAILED"
        except KeyError:
            smart_test_status = "NA"
        health_data["SMART_health"] = smart_test_status
        smart_required_attributes = set(["Reallocated_Sector_Ct", "Spin_Retry_Count", "Current_Pending_Sector", "Offline_Uncorrectable"])
        try:
            for attribute in response["ata_smart_attributes"]["table"]:
                try:
                    if attribute["name"] in smart_required_attributes:
                        health_data[attribute["name"]] = attribute["raw"]["value"]
                except KeyError:
                    pass
        except KeyError:
            pass
        return health_data

    def _is_local_drive(self):
        """
        Detect Node server local drives using Hdparm tool.

        Hdparm tool give information only for node drive.
        For external JBOD/virtual drives it will give output as:
        "SG_IO: bad/missing sense data "
        Hdparm does not have support for NVME drives, for this drives it gives o/p as:
        "failed: Inappropriate ioctl for device"
        """
        DISK_ERR_MISSING_SENSE_DATA = "SG_IO: bad/missing sense data"
        DISK_ERR_GET_ID_FAILURE = "HDIO_GET_IDENTITY failed: Invalid argument"
        cmd = f'sudo hdparm -i {self.device}'
        _, err, retcode = SimpleProcess(cmd).run()

        if retcode == 0:
            return True
        else:
            # TODO : In case of different error(other than \
            # "SG_IO: bad/missing sense data") for local drives,
            # this check would fail.
            if DISK_ERR_MISSING_SENSE_DATA not in err and \
               DISK_ERR_GET_ID_FAILURE not in err:
                return True
            else:
                return False

    @classmethod
    def get_disks(cls):
        bus = SystemBus()
        # Obtain a disk manager interface for monitoring drives
        disk_manager = Interface(bus.get_object('org.freedesktop.UDisks2',
                                                '/org/freedesktop/UDisks2'),
                                 dbus_interface='org.freedesktop.DBus.ObjectManager')

        # Dict of drives by-path symlink from systemd
        drive_by_path = {}

        # Dict of drives by device name from systemd
        drive_by_device_name = {}

        disk_objects = disk_manager.GetManagedObjects()

        # Get a list of all the block devices available in systemd
        re_blocks = re.compile('(?P<path>.*?/block_devices/(?P<id>.*))')
        block_devs = [m.groupdict() for m in
                      [re_blocks.match(path) for path in list(disk_objects.keys())]
                      if m]

        # Retrieve the by-id symlink for each drive and save in a dict with the drive path as key
        for block_dev in block_devs:
            try:
                if disk_objects[block_dev['path']].get('org.freedesktop.UDisks2.Block') is not None:
                    # Obtain the list of symlinks for the block device
                    udisk_block = disk_objects[block_dev['path']]["org.freedesktop.UDisks2.Block"]
                    symlinks = cls._sanitize_dbus_value(udisk_block["Symlinks"])

                    # Parse out the wwn symlink if it exists otherwise use the by-id
                    for symlink in symlinks:
                        # TODO:  Improve logic for getting resource_id
                        # Current approch for getting resource_id is to check "phy" in by-path
                        # symlink. If "phy" is in by-path use path of that drive for resource_id
                        if "by-path" in symlink:
                            drive_by_path[udisk_block["Drive"]] = symlink[len("/dev/disk/by-path/"):]

                    # Maintain a dict of device names
                    device = cls._sanitize_dbus_value(udisk_block["Device"])
                    drive_by_device_name[udisk_block["Drive"]] = device

            except Exception as ae:
                # block_dev unusable
                print("block_dev unusable: %r" % ae)

        disks = []

        for obj_path, interfaces_and_property in disk_manager.GetManagedObjects().items():
            if "drive" in obj_path and cls.is_physical_drive(interfaces_and_property["org.freedesktop.UDisks2.Drive"]):
                disk = cls(interfaces_and_property["org.freedesktop.UDisks2.Drive"]["Id"],
                           drive_by_path.get(obj_path, interfaces_and_property["org.freedesktop.UDisks2.Drive"]["Id"]),
                           drive_by_device_name[obj_path])
                disks.append(disk)
        return disks

    @staticmethod
    def is_physical_drive(interfaces_and_property):
        """
        Get the physical drives attached to server.

        WWN is 32 hex characters for the disk which is attached through RAID
        controller and starts with 0x6. In JBOD setup drives will be directly
        attached to server so it's WWN will be 16 hex charactes and will starts with 0x5
        In JBOD setup this will return server+storage_enclosure drive and in normal
        setup this will return only server drives.

        Drives from JBOD setup (all drives start with 0x5)
        [0:0:1:0]    disk    0x5000c500adff06d3                  /dev/sdb
        [0:0:2:0]    disk    0x5000c500ae9e483f                  /dev/sdc
        [0:0:3:0]    disk    0x5000c500adfed4df                  /dev/sdd

        Drives from non-JBOD setup (drives coming from enclosure starts with 0x6,
                                server drives start with 0x5)
        [0:0:0:0]    disk    0x5000c500c2ecc4b8                  /dev/sda
        [1:0:0:0]    disk    0x5000c500c2ec508b                  /dev/sdbn
        [6:0:1:1]    disk    0x600c0ff00050f0bb13c7505f02000000  /dev/sdr
        """
        return interfaces_and_property["WWN"].startswith("0x5")

    @classmethod
    def _sanitize_dbus_value(cls, value):
        """Convert certain DBus type combinations so that they are easier to read."""
        if isinstance(value, Array) and value.signature == "ay":
            try:
                return cls._decode_ay(value)
            except Exception:
                # Try an array of arrays; 'aay' which is the symlinks
                return list(map(cls._decode_ay, value or ()))
        elif isinstance(value, Array) and value.signature == "y":
            return bytearray(value).rstrip(bytearray((0,))).decode('utf-8')
        else:
            return value

    @staticmethod
    def _decode_ay(value):
        """Convert binary blob from DBus queries to strings."""
        if len(value) == 0 or \
           value is None:
            return ''
        elif isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            return value.decode('utf-8')
        else:
            # dbus.Array([dbus.Byte]) or any similar sequence type:
            return bytearray(value).rstrip(bytearray((0,))).decode('utf-8')
