#!/usr/bin/env python3

from tkinter import *
from subprocess import *
from tkinter import ttk
from tkinter.font import Font
from tkinter import messagebox, simpledialog, ttk
from tkinter.simpledialog import Dialog
from tkinter import filedialog
import multiprocessing as mp
import threading
import subprocess
import time
import datetime
import os
import shutil
import queue
import asyncio
from distutils.dir_util import copy_tree
from subprocess import check_output, CalledProcessError


def update_device_list():
    result = subprocess.run(
        ["lsblk", "-o", "NAME,TYPE", "-r"], capture_output=True, text=True
    )
    devices = [
        line.split()[0]
        for line in result.stdout.split("\n")
        if len(line.split()) > 1 and line.split()[1] == "disk"
    ]
    clone_combo["values"] = devices


def update_device_list1():
    result = subprocess.run(
        ["lsblk", "-o", "NAME,TYPE", "-r"], capture_output=True, text=True
    )
    devices = [
        line.split()[0]
        for line in result.stdout.split("\n")
        if len(line.split()) > 1 and line.split()[1] == "disk"
    ]
    device_combo["values"] = devices


def select_image():
    filetypes = [("Image Files", "*.img")]
    image_file = filedialog.askopenfilename(filetypes=filetypes)
    if image_file:
        image_label["text"] = image_file


def select_output_folder():
    output_folder = filedialog.askdirectory()
    if output_folder:
        output_folder_label["text"] = output_folder


async def progress_bar_update(progress_bar, dd_thread, progress_window, progress_queue):
    while dd_thread.is_alive():
        if progress_bar["value"] < 100:
            progress_bar["value"] += 1
            progress_bar.update()
        await asyncio.sleep(0.1)
    progress_window.destroy()


async def dd_copy(device, image_file, progress_queue):
    # Create the image using dd command
    dd_command = [
        "sudo",
        "dd",
        f"if=/dev/{device}",
        f"of={image_file}",
        "bs=512k",
        "status=progress",
    ]
    dd_process = subprocess.Popen(
        dd_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Update the progress queue with the percent complete
    for line in dd_process.stderr:
        if b"bytes" in line:
            parts = line.split()
            try:
                progress = int(parts[0])
                total = int(parts[2])
                percent = int((progress / total) * 100)
                await progress_queue.put(percent)  # use asyncio to update the queue
            except (IndexError, ValueError):
                continue

    dd_process.wait()


async def create_image():
    # Get the selected output folder and device
    output_folder = output_folder_label["text"]
    device = device_combo.get()

    if not output_folder:
        messagebox.showerror("Error", "No output folder selected.")
        return
    if not device:
        messagebox.showerror("Error", "No device selected.")
        return

    # Get the current date and time to use in the image file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    image_file = os.path.join(output_folder, f"{device}_{timestamp}.img")

    # Confirm the image creation operation
    confirmed = messagebox.askyesno(
        "Confirm Image Creation",
        f"Are you sure you want to create an image at {image_file}?",
    )
    if not confirmed:
        return

    # Create a progress bar to show the progress of dd command
    progress_window = Toplevel(root)
    progress_window.title("Image Creation Progress")
    progress_bar = ttk.Progressbar(
        progress_window, orient="horizontal", length=400, mode="indeterminate"
    )
    progress_bar.pack(padx=10, pady=10)
    progress_bar.start()

    # Create a queue to store progress updates
    progress_queue = asyncio.Queue()

    # Start the dd coroutine in a separate thread
    def run_dd():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dd_copy(device, image_file, progress_queue))
        loop.close()

    thread = threading.Thread(target=run_dd)
    thread.start()

    # Update the progress bar with values from the queue
    while thread.is_alive():
        try:
            percent = progress_queue.get_nowait()
            progress_bar["value"] = percent
            progress_bar.update()
        except asyncio.QueueEmpty:
            pass
        root.update()

    # Stop the progress bar
    progress_bar.stop()

    # Close the progress window
    progress_window.destroy()

    messagebox.showinfo(
        "Image Creation Complete", f"Image has been created at {image_file}"
    )


async def cloning(dd_command,progress_queue):
    dd_process = await asyncio.create_subprocess_exec(
        *dd_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    while True:
        line = await dd_process.stdout.readline()
        if not line:
            break
        line = line.decode().strip()
        if "bytes" in line:
            parts = line.split()
            progress = parts[0]
            total = parts[2]
            percent = int((int(progress) / int(total)) * 100)
            progress_bar["value"] = percent
            progress_bar.update()
        await asyncio.sleep(0.01)
    await dd_process.wait()
    messagebox.showinfo("Clone Complete", "Device cloning has been completed.")
    progress_window.destroy()


async def start_cloning():
    # Get the selected image file and device
    image_file = image_label["text"]
    device = clone_combo.get()

    if not image_file:
        messagebox.showerror("Error", "No image file selected.")
        return
    if not device:
        messagebox.showerror("Error", "No device selected.")
        return

    # Confirm the cloning operation
    confirmed = messagebox.askyesno(
        "Confirm Clone", f"Are you sure you want to clone /dev/{device} with {image_file}?"
    )
    if not confirmed:
        return

    # Remove partition information from the device
    partitions = subprocess.run(
        ["sudo", "sfdisk", "--delete", f"/dev/{device}", "--force"],
        capture_output=True,
        text=True,
    )
    if partitions.returncode != 0:
        messagebox.showerror("Error", partitions.stderr)
        return

    # Create a progress bar to show the progress of dd command
    progress_window = Toplevel(root)
    progress_window.title("Cloning Progress")
    progress_bar = ttk.Progressbar(
        progress_window, orient="horizontal", length=400, mode="indeterminate"
    )
    progress_bar.pack(padx=10, pady=10)
    progress_bar.start()

    progress_queue = asyncio.Queue()
    # Start the dd thread
    dd_command = [
        "sudo",
        "dd",
        f"if={image_file}",
        f"of=/dev/{device}",
        "bs=512k",
        "status=progress",
    ]
    def run_clone():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cloning(dd_command, progress_queue))
        loop.close()

    thread = threading.Thread(target=run_clone)
    thread.start()

    while thread.is_alive():
        try:
            percent = progress_queue.get_nowait()
            progress_bar["value"] = percent
            progress_bar.update()
        except asyncio.QueueEmpty:
            pass
        root.update()
    # Stop the progress bar
    progress_bar.stop()

    # Close the progress window
    progress_window.destroy()

    messagebox.showinfo(
        "Drive Clone Complete", f"Image file has been cloned to /dev/{device}"
    )

async def clone_confirmation():
    # Show a message box to confirm cloning
    confirmed = messagebox.askyesno(
        "Confirm Clone", "Are you sure you want to clone the device?"
    )
    if confirmed:
        await start_cloning()

async def create_confirmation():
    # Show a message box to confirm creating the image
    confirmed = messagebox.askyesno(
        "Confirm Image Creation",
        f"Are you sure you want to create an image from {device_combo.get()}?",
    )
    if confirmed:
        await create_image()

if __name__ == "__main__":
    # Create the main window
    root = Tk()
    root.title("USB CLONE")
    root.geometry("500x500")
    heading_font = Font(family="Courier", size=20, weight="bold")
    notebook = ttk.Notebook(root)
    notebook.pack(fill=BOTH, expand=True)

    # Create the "Clone" tab
    clone_tab = Frame(notebook)
    notebook.add(clone_tab, text="Clone")
    heading_label = Label(clone_tab, text="CLONE DRIVE", font=heading_font)
    heading_label.pack(pady=(20, 10))
    device_label = Label(clone_tab, text="Select a device:")
    device_label.pack()
    clone_combo = ttk.Combobox(clone_tab, values=[], state="readonly")
    clone_combo.pack()
    image_label = Label(clone_tab, text="No image selected")
    image_label.pack(pady=(10, 0))
    image_button = Button(clone_tab, text="Select Image", command=select_image)
    image_button.pack(pady=(10, 0))
    refresh_button = Button(clone_tab, text="Refresh", command=update_device_list)
    refresh_button.pack(pady=(10, 0))
    update_device_list()
    clone_button = Button(
        clone_tab, text="clone", command=lambda: asyncio.run(clone_confirmation())
    )
    clone_button.pack(pady=(10, 0))

    # Create the "Copy Routes" tab
    create_image_tab = Frame(notebook)
    notebook.add(create_image_tab, text="Copy Routes")


    # Create the "Create Image" tab
    create_image_tab = Frame(notebook)
    notebook.add(create_image_tab, text="Create Image")
    heading_label = Label(create_image_tab, text="CREATE IMAGE", font=heading_font)
    heading_label.pack(pady=(20, 10))
    device_label = Label(create_image_tab, text="Select a device:")
    device_label.pack()
    device_combo = ttk.Combobox(create_image_tab, values=[], state="readonly")
    device_combo.pack()
    output_folder_label = Label(create_image_tab, text="Select an output folder:")
    output_folder_label.pack()
    output_folder_button = Button(
        create_image_tab, text="Select Output Folder", command=select_output_folder
    )
    output_folder_button.pack()
    refresh_button = Button(create_image_tab, text="Refresh", command=update_device_list1)
    refresh_button.pack(pady=(10, 0))
    create_button = Button(
        create_image_tab, text="Create", command=lambda: asyncio.run(create_confirmation())
    )
    create_button.pack(pady=(10, 0))
    update_device_list1()

    root.mainloop()