from logging import basicConfig, getLogger, INFO
from os import environ, system, listdir
from subprocess import check_output
from sys import exit
from pathlib import PurePath


class Volume:
    def __init__(self, label):
        """Stores label, password and initiates logging."""
        basicConfig(format='Method: %(funcName)s - Line: %(lineno)d - %(message)s', level=INFO)
        self.logger = getLogger(PurePath(__file__).stem)  # gets the current file name
        self.volume_label = label
        self.password = environ.get('PASSWORD')
        self.mount_uuid = None

    def stop_usage(self):
        if self.volume_label not in listdir('/Volumes'):
            exit(f'{self.volume_label} is not connected to/mounted on your {Helper.device_model()}.')
        if not self.password:
            exit("Add 'PASSWORD={YOUR SYSTEM PASSWORD}' as env variable to stop disk usage.")
        pid_check = check_output(f"echo {self.password} | sudo -S lsof '/Volumes/{self.volume_label}' 2>&1;",
                                 shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        self.logger.info(f'Number of processes using {self.volume_label}: {len(pid_list) - 1}')
        for id_ in pid_list:
            system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1') if id_ else None
        self.logger.info(f'{len(pid_list) - 1} active processes have been terminated.')

    def unmount_disk(self):
        self.logger.info('Accessing stop_usage')
        Volume(label=self.volume_label).stop_usage()
        disk_check = check_output(f"diskutil list 2>&1;", shell=True)
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
                                     f'{Helper.device_model()}')
                    break

    def mount_disk_by_uuid(self):
        if self.mount_uuid:
            system(f'diskutil mountDisk {self.mount_uuid} > /dev/null 2>&1;')  # mount using disk volume/UUID
        else:
            self.logger.info('Accessing mount_disk_by_label')
            Volume(label=self.volume_label).mount_disk_by_label()

    def mount_disk_by_label(self):
        logger = getLogger('mount_disk_by_label')
        system(f'diskutil mount "{self.volume_label}" > /dev/null 2>&1;')  # mount using disk label
        Helper.check(volume_label=self.volume_label, logger=logger)


class Helper:
    @staticmethod
    def extract_str(input_):
        """Extracts strings from the received input"""
        return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']])

    @staticmethod
    def device_model():
        """Returns required info either model or the version of the PC"""
        device = (check_output("sysctl hw.model", shell=True)).decode('utf-8').split('\n')  # gets model info
        result = list(filter(None, device))[0]  # removes empty string ('\n')
        model = Helper.extract_str(result).replace('hwmodel', '').strip()
        return model

    @staticmethod
    def check(volume_label, logger):
        if volume_label in listdir('/Volumes'):
            logger.info(f'Disk {volume_label} has been mounted on your {Helper.device_model()}')
        else:
            logger.info(f'{volume_label} is not connected or mounted on your {Helper.device_model()}.')
