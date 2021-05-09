#!/usr/bin/env python3

from tkinter import *
from subprocess import *
from tkinter import messagebox, simpledialog, ttk
from tkinter.simpledialog import Dialog
import threading
import time
import os
import shutil
from distutils.dir_util import copy_tree
from subprocess import check_output, CalledProcessError


def wait_clone():
    """Creates a new window to let the user know to wait while dd runs."""
    global please_wait
    please_wait = Toplevel(screen)
    please_wait.title("Please wait")
    please_wait.geometry('250x100')

    wait_lable = Label(please_wait, text="Please wait...")
    wait_lable.pack(pady=20)
    p1 = ttk.Progressbar(please_wait, length=200, mode="determinate",
                         orient=HORIZONTAL)
    p1.pack()
    p1.start(25)

    start_clone = threading.Thread(target=clone_combined)
    start_clone.daemon = True
    start_clone.start()


def schedule_wait():
    """Creates a new window to let the user know to wait while schedules are deleted and copied."""
    global schedule_w
    schedule_w = Toplevel(screen)
    schedule_w.title("Please wait")
    schedule_w.geometry('250x100')

    wait_lable = Label(schedule_w, text="Please wait...")
    wait_lable.pack(pady=20)
    p1 = ttk.Progressbar(schedule_w, length=200, mode="determinate",
                         orient=HORIZONTAL)
    p1.pack()
    p1.start(25)

    copyschedule = threading.Thread(target=copy_schedule)
    copyschedule.daemon = True
    copyschedule.start()


def clone_combined():
    """All required clone functions combined."""
    fromDirectory = "/home/driveBU/schedule"
    toDirectory = "/media/newdrive/schedule"
    format_drive()
    version()
    time.sleep(5)
    mount_dest()
    time.sleep(3)
    delete()
    time.sleep(6)
    copy_tree(fromDirectory, toDirectory)
    finished_ok = messagebox.showinfo("Complete", "Click ok to close")
    screen.destroy()


def version():
    """Sets the proper image path based on checkbox selection."""
    if version_checkbox == True:
        v1 = 'dd if=/home/driveBU/version1.img of=/dev/sdb bs=512k oflag=direct status=progress'
        l = Popen('echo %s|sudo -S %s' %
                  (sudoPassword, v1), shell=True, stdout=PIPE)
        l.wait()
    else:
        v2 = 'dd if=/home/driveBU/version2.img of=/dev/sdb bs=512k oflag=direct status=progress'
        s = Popen('echo %s|sudo -S %s' %
                  (sudoPassword, v2), shell=True, stdout=PIPE)
        s.wait()


def copy_schedule():
    """Deletes schedule folder from drive and copies current schedule folder"""
    fromDirectory = "/home/driveBU/schedule"
    toDirectory = "/media/newdrive/schedule"
    mount_dest()
    time.sleep(3)
    delete()
    time.sleep(6)
    copy_tree(fromDirectory, toDirectory)
    schedule_w.destroy()
    copy_complete = messagebox.showinfo("Complete", "schedules have been copied")
    screen.deiconify()
    copyr.destroy()


def clone():
    """Will confim with user they are ready to clone the drive then clone."""
    ready_message = messagebox.askquestion(
        "Ready?", "Are you sure? This process can take 2+ hours")
    if ready_message == 'yes':
        confirm_message = messagebox.askokcancel(
            "Ready", "Turn on USB adapter power switch and click ok.")
        if confirm_message == 1:
            wait_clone()
        else:
            screen.destroy()


def format_drive():
    """Removes parition tables and formats drive. Complete format before DD because sometime it would mess up with just a wipe and DD"""
    umountDest = 'umount /dev/sdb?*'
    deletePartition = 'wipefs -a /dev/sdb'
    formatDrive = 'mkfs.ext3 -F /dev/sdb'
    um = Popen('echo %s|sudo -S %s' %
               (sudoPassword, umountDest), shell=True, stdout=PIPE)
    um.wait()
    wp = Popen('echo %s|sudo -S %s' %
               (sudoPassword, deletePartition), shell=True, stdout=PIPE)
    wp.wait()
    fd = Popen('echo %s|sudo -S %s' %
               (sudoPassword, formatDrive), shell=True, stdout=PIPE)
    fd.wait()


def mount_dest():
    """Mounts Destination to exspected mount point."""
    umountDest = 'umount /dev/sdb?*'
    mountDest = 'mount /dev/sdb1 /media/newdrive'
    um = Popen('echo %s|sudo -S %s' %
               (sudoPassword, umountDest), shell=True, stdout=PIPE)
    um.wait()
    md = Popen('echo %s|sudo -S %s' %
               (sudoPassword, mountDest), shell=True, stdout=PIPE)
    md.wait()


def delete():
    """Deletes the schedule folder from drive"""
    path = os.path.join('/media/newdrive/schedule', 'SQL')
    shutil.rmtree(path)


def copy_schedule_window():
    """New window for copying schedules instructions"""
    global copyr
    copyr = Toplevel()
    copyr.geometry("500x500")
    copyr.title("Schedule")
    heading = Label(copyr, text="COPY SCHEDULES",
                    fg="black", bg="grey", width="500", height="3",)
    heading.config(font=("Courier", 20, 'bold'))
    heading.pack()
    step1_label = Label(copyr, text="1. Remove all USB drives from computer.")
    step1_label.pack(ipady=10)
    step2_label = Label(
        copyr, text="2. Attach the ACFT drive to the USB adapter.")
    step2_label.pack(ipady=10)
    step3_label = Label(
        copyr, text="3. Plug the USB adapter into the computer.")
    step3_label.pack(ipady=10)
    step4_label = Label(
        copyr, text="4. USB adapter power switch ON then click ok.")
    step4_label.pack(ipady=10)
    copy_schedule_button = Button(
        copyr, text="Ok", bg="grey", command=schedule_wait)
    copy_schedule_button.pack()
    cancel_schedule_button = Button(
        copyr, text="Cancel", bg="grey", command=cancel_route_copy)
    cancel_schedule_button.pack()

    
def cancel_route_copy():
    screen.deiconify()
    copyr.destroy()


screen = Tk()
screen.eval('tk::PlaceWindow %s center' %
            screen.winfo_pathname(screen.winfo_id()))
sudoPassword = "Password"


# Creates the main from window
screen.geometry("500x500")
screen.title("USB CLONE")
heading = Label(text="CLONE DRIVE", fg="black",
                bg="grey", width="500", height="3",)
heading.config(font=("Courier", 20, 'bold'))
heading.pack()


# Labels for entry boxes
step1_label = Label(text="1. Remove all USB drives from computer.")
step1_label.pack(ipady=10)
step2_label = Label(text="2. Attach the ACFT drive to the USB adapter.")
step2_label.pack(ipady=10)
step3_label = Label(text="3. Plug the USB adapter into the computer.")
step3_label.pack(ipady=10)
step4_label = Label(text="4. DO NOT turn the power switch on yet.")
step4_label.pack(ipady=10)
step5_label = Label(text="5. Click Clone and follow the prompts.")
step5_label.pack(ipady=10)


# Creates buttons.
version_checkbox = Checkbutton(
    screen, text="Version1 Drive?", variable=version)
version_checkbox.pack()
clone_button = Button(screen, text="Clone", width="7",
                      bg="grey", command=clone)
clone_button.pack()
copy_schedule_button = Button(
    screen, text="Copy schedule", bg="grey", command=copy_schedule_window)
copy_schedule_button.pack()


screen.mainloop()
