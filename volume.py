from subprocess import check_output
from os import environ, system
volume_label = input("Enter the name of the Volume you'd like to handle:\n")
pid_check = check_output(f"echo {environ.get('PASSWORD')} | sudo -S lsof /Volumes/{volume_label} 2>&1;", shell=True)
pid_list = pid_check.decode('utf-8').split('\n')
for id_ in pid_list:
    system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1') if id_ else None

disk_check = check_output(f"diskutil list 2>&1;", shell=True)
disk_list = disk_check.decode('utf-8').split('\n\n')
condition = '(external, physical):'
mount_uuid = None
for disk in disk_list:
    if disk and condition in disk:
        unmount_uuid = disk.split('\n')[0].strip(condition)
        disk_info = disk.split('\n')[-1].split()
        if volume_label in disk_info:
            mount_value = unmount_uuid
            system(f'diskutil unmountDisk {unmount_uuid} > /dev/null 2>&1;')

system(f'diskutil mountDisk {mount_uuid} > /dev/null 2>&1;')  # mount by disk volume/UUID
system(f'diskutil mount {volume_label} > /dev/null 2>&1;')  # mount by disk label
