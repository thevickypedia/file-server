from logging import INFO, basicConfig, getLogger
from os import environ, listdir, system
from pathlib import PurePath
from subprocess import check_output
from sys import exit


class Volume:
    """Initiates Volume object to mount, unmount and stop the disk usage.

    >>> Volume

    """

    def __init__(self, label):
        """Stores label, password and initiates logging.

        Args:
            label: Name of the volume connected.
        """
        basicConfig(format="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
                    level=INFO)
        self.logger = getLogger(PurePath(__file__).stem)  # gets the current file name
        self.volume_label = label
        self.password = environ.get('PASSWORD')
        self.mount_uuid = None

    def stop_usage(self) -> None:
        """Kills all the background processes utilizing the volume to stop the disk usage."""
        if self.volume_label not in listdir('/Volumes'):
            exit(f'{self.volume_label} is not connected to/mounted on your {device_model()}.')
        if not self.password:
            exit("Add 'PASSWORD={YOUR SYSTEM PASSWORD}' as env variable to stop disk usage.")
        pid_check = check_output(f"echo {self.password} | sudo -S lsof '/Volumes/{self.volume_label}' 2>&1;",
                                 shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        self.logger.info(f'Number of processes using {self.volume_label}: {len(pid_list) - 1}')
        for id_ in pid_list:
            system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1') if id_ else None
        self.logger.info(f'{len(pid_list) - 1} active processes have been terminated.')

    def unmount_disk(self) -> None:
        """Ejects the disk from parent device."""
        self.logger.info('Accessing stop_usage')
        self.stop_usage()
        disk_check = check_output("diskutil list 2>&1;", shell=True)
        disk_list = disk_check.decode('utf-8').split('\n\n')
        condition = '(external, physical):'
        for disk in disk_list:
            if disk and condition in disk:
                unmount_uuid = disk.split('\n')[0].strip(condition)
                disk_info = disk.split('\n')[-1]
                if self.volume_label in disk_info:
                    self.mount_uuid = unmount_uuid
                    system(f'diskutil unmountDisk {unmount_uuid} > /dev/null 2>&1;')
                    self.logger.info(f'Disk {unmount_uuid} with Name {self.volume_label} has been unmounted from your '
                                     f'{device_model()}')
                    break

    def mount_disk_by_uuid(self) -> None:
        """Tries to mount the disk using UUID which is updated by the `unmount_disk` function.

        Calls `mount_disk_by_label` if UUID is None.
        """
        if self.mount_uuid:
            system(f'diskutil mountDisk {self.mount_uuid} > /dev/null 2>&1;')  # mount using disk volume/UUID
        else:
            self.logger.info('Accessing mount_disk_by_label')
            self.mount_disk_by_label()

    def mount_disk_by_label(self) -> None:
        """Uses a terminal command to mount the disk using the volume name."""
        system(f'diskutil mount "{self.volume_label}" > /dev/null 2>&1;')  # mount using disk label
        if self.volume_label in listdir('/Volumes'):
            self.logger.info(f'Disk {self.volume_label} has been mounted on your {device_model()}')
        else:
            self.logger.info(f'{self.volume_label} is not connected or mounted on your {device_model()}.')


def extract_str(input_) -> str:
    """Extracts strings from the received input.

    Args:
        input_: Un-formatted string.

    Returns:
        str:
        A perfect string.

    """
    return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']])


def device_model() -> str:
    """Uses `sysctl` command to get the device model and version information.

    Returns:
        str:
        Model of the parent device.

    """
    device = (check_output("sysctl hw.model", shell=True)).decode('utf-8').split('\n')  # gets model info
    result = list(filter(None, device))[0]  # removes empty string ('\n')
    model = extract_str(result).replace('hwmodel', '').strip()
    return model
