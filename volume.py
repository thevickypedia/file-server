from subprocess import check_output
import os
volume_name = input("Enter the Volume Name you'd like to kill usage for:\n")
pid_check = check_output(f"lsof /Volumes/{volume_name}", shell=True)
pid_list = pid_check.decode('utf-8').split('\n')
for id_ in pid_list:
    os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout

disk_check = check_output(f"diskutil list 2>&1;", shell=True)
disk_list = disk_check.decode('utf-8').split('\n\n')
condition = '(external, physical):'
for disk in disk_list:
    if disk and condition in disk:
        unmount_value = disk.split('\n')[0].strip(condition)
        disk_info = disk.split('\n')[-1].split()
        if volume_name in disk_info:
            os.system(f'diskutil unmountDisk {unmount_value} 2>&1;')
