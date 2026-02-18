import socket
import tkinter as tk
from tkinter import filedialog, ttk
import os

# =========================
# НАСТРОЙКИ
# =========================

TEACHER_IP = "172.20.10.14"
TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 4096

ADMIN_MODE = False
DISCOVERED_CLIENTS = []

# =========================
# UDP DISCOVERY
# =========================

def discover_servers():
    global DISCOVERED_CLIENTS
    DISCOVERED_CLIENTS.clear()

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(1)

    try:
        udp.sendto(b"DISCOVER_SERVER", ("<broadcast>", UDP_PORT))

        while True:
            try:
                data, addr = udp.recvfrom(1024)
                if data == b"SERVER_HERE":
                    ip = addr[0]
                    if ip != TEACHER_IP:
                        DISCOVERED_CLIENTS.append(ip)
            except:
                break
    except:
        pass

    udp.close()
    update_device_list()

# =========================
# ОТПРАВКА ФАЙЛА
# =========================

def send_file(target_ip):
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)

    try:
        s = socket.socket()
        s.connect((target_ip, TCP_PORT))

        s.send(f"{filename}|{filesize}".encode())

        with open(file_path, "rb") as f:
            sent = 0
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                s.sendall(data)
                sent += len(data)
                progress["value"] = (sent / filesize) * 100
                root.update_idletasks()

        s.close()
        progress["value"] = 0

    except Exception as e:
        print("Ошибка отправки:", e)

def send_to_all():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    targets = [TEACHER_IP] + DISCOVERED_CLIENTS

    for ip in targets:
        send_file_to_target(ip, file_path)

def send_file_to_target(target_ip, file_path):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)

    try:
        s = socket.socket()
        s.connect((target_ip, TCP_PORT))

        s.send(f"{filename}|{filesize}".encode())

        with open(file_path, "rb") as f:
            sent = 0
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                s.sendall(data)
                sent += len(data)
                progress["value"] = (sent / filesize) * 100
                root.update_idletasks()

        s.close()
        progress["value"] = 0

    except Exception as e:
        print(f"Ошибка отправки на {target_ip}:", e)

# =========================
# GUI ФУНКЦИИ
# =========================

def update_device_list():
    device_list.delete(0, tk.END)
    device_list.insert(tk.END, f"Учительский ({TEACHER_IP})")

    if ADMIN_MODE:
        for ip in DISCOVERED_CLIENTS:
            device_list.insert(tk.END, f"Клиент ({ip})")
        send_all_button.pack(pady=5)
    else:
        send_all_button.pack_forget()

def enable_admin_mode(event=None):
    global ADMIN_MODE
    ADMIN_MODE = True
    discover_servers()

def hotkey_send_all(event=None):
    if ADMIN_MODE:
        send_to_all()

def send_selected():
    selection = device_list.curselection()

    if not selection:
        target_ip = TEACHER_IP
    else:
        text = device_list.get(selection[0])
        target_ip = text.split("(")[1][:-1]

    send_file(target_ip)

# =========================
# ОКНО
# =========================

root = tk.Tk()
root.title("INFObot 2.0")
root.geometry("900x550")
root.configure(bg="#1e1e1e")

root.bind("<Control-Shift-W>", enable_admin_mode)
root.bind("<Control-Shift-A>", hotkey_send_all)

# =========================
# ЗАГОЛОВКИ
# =========================

title_label = tk.Label(
    root,
    text="ЗАГОЛОВОК",
    font=("Arial", 28, "bold"),
    fg="white",
    bg="#1e1e1e"
)
title_label.pack(pady=20)

subtitle_label = tk.Label(
    root,
    text="Подзаголовок",
    font=("Arial", 16),
    fg="#aaaaaa",
    bg="#1e1e1e"
)
subtitle_label.pack(pady=5)

# =========================
# СПИСОК УСТРОЙСТВ
# =========================

device_list = tk.Listbox(
    root,
    font=("Arial", 12),
    width=40,
    height=6
)
device_list.pack(pady=20)

# =========================
# ПРОГРЕСС БАР
# =========================

progress = ttk.Progressbar(
    root,
    orient="horizontal",
    length=400,
    mode="determinate"
)
progress.pack(pady=10)

# =========================
# КНОПКИ
# =========================

send_button = tk.Button(
    root,
    text="Отправить файл",
    bg="#2ecc71",
    fg="white",
    font=("Arial", 14, "bold"),
    width=20,
    height=2,
    command=send_selected
)
send_button.pack(pady=15)

send_all_button = tk.Button(
    root,
    text="Отправить ВСЕМ",
    bg="#27ae60",
    fg="white",
    font=("Arial", 12, "bold"),
    width=18,
    height=2,
    command=send_to_all
)

# =========================

update_device_list()

root.mainloop()
