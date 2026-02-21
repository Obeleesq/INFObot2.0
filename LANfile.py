import socket
import threading
import os
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# ================= НАСТРОЙКИ =================

TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 4096
CONFIG_FILE = "config.json"
DEFAULT_TEACHER_IP = "172.20.10.14"

# ================= CONFIG =================

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"teacher_ip": DEFAULT_TEACHER_IP}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

config = load_config()
TEACHER_IP = config["teacher_ip"]

# ================= ГЛОБАЛЬНЫЕ =================

devices = []
advanced_mode = False
save_folder = str(Path.home() / "Desktop")

# ================= GUI =================

root = tk.Tk()
root.title("INFObot 4.0")
root.geometry("900x600")
root.resizable(False, False)

# ===== LEFT SIDE (CLIENT) =====

left_frame = tk.Frame(root)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

title_label = tk.Label(left_frame, text="ФАЙЛОГРАМ", font=("Arial", 18, "bold"))
title_label.pack(pady=5)

subtitle_label = tk.Label(left_frame, text="Отправь файлы по локальной сети (меганайт)", font=("Arial", 12))
subtitle_label.pack(pady=5)

device_listbox = tk.Listbox(left_frame, width=50, height=15)
device_listbox.pack(pady=10)

button_frame = tk.Frame(left_frame)
button_frame.pack(pady=10)

send_button = tk.Button(button_frame, text="Отправить файл", bg="green", fg="white", width=20)
send_button.grid(row=0, column=0, padx=5)

send_all_button = tk.Button(button_frame, text="Отправить всем", bg="green", fg="white", width=20)

# ===== RIGHT SIDE (SERVER) =====

right_frame = tk.Frame(root)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

choose_button = tk.Button(right_frame, text="Выбрать папку сохранения")
choose_button.pack(pady=5)

folder_label = tk.Label(right_frame, text=f"Путь: {save_folder}")
folder_label.pack()

log_box = scrolledtext.ScrolledText(right_frame, width=50, height=20)
log_box.pack(pady=10)

# ================= ЛОГ =================

def log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

# ================= TCP SERVER =================

def handle_client(conn, addr):
    global save_folder
    try:
        log(f"Подключение от {addr}")

        name_size_bytes = conn.recv(4)
        if not name_size_bytes:
            log("Ошибка получения размера имени")
            return

        name_size = int.from_bytes(name_size_bytes, 'big')
        filename = conn.recv(name_size).decode("utf-8")
        filename = os.path.basename(filename)

        filepath = os.path.join(save_folder, filename)
        log(f"Сохраняю файл: {filepath}")

        with open(filepath, "wb") as f:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

        log("[✓] Файл успешно получен")

    except Exception as e:
        log(f"Ошибка: {e}")
    finally:
        conn.close()

def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", TCP_PORT))
    server.listen(5)
    log(f"[TCP] Сервер запущен на порту {TCP_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ================= UDP DISCOVERY =================

def udp_discovery():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", UDP_PORT))
    log(f"[UDP] Discovery активен на порту {UDP_PORT}")

    while True:
        data, addr = udp.recvfrom(1024)
        if data.decode() == "DISCOVER_INFOBOT":
            udp.sendto(b"INFOBOT_HERE", addr)

# ================= DISCOVER CLIENT =================

def discover_devices():
    global devices
    devices = []
    devices.append(("Черепной ноутбук", TEACHER_IP))

    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.settimeout(1)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.sendto(b"DISCOVER_INFOBOT", ("<broadcast>", UDP_PORT))

        while True:
            try:
                data, addr = udp.recvfrom(1024)
                if addr[0] != TEACHER_IP:
                    devices.append((addr[0], addr[0]))
            except socket.timeout:
                break
    except:
        pass

    update_device_list()

def update_device_list():
    device_listbox.delete(0, tk.END)
    for name, ip in devices:
        if name == "Черепной ноутбук":
            device_listbox.insert(tk.END, f"{name} ({ip})")
        elif advanced_mode:
            device_listbox.insert(tk.END, ip)

# ================= SEND =================

def send_file_to(ip, filepath):
    try:
        filename = os.path.basename(filepath)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, TCP_PORT))

        name_bytes = filename.encode("utf-8")
        s.send(len(name_bytes).to_bytes(4, 'big'))
        s.send(name_bytes)

        with open(filepath, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                s.send(data)

        s.close()
        log(f"[→] Файл отправлен на {ip}")

    except Exception as e:
        messagebox.showerror("Ошибка", f"{ip}\n{e}")

def send_selected():
    selection = device_listbox.curselection()
    if not selection:
        messagebox.showwarning("Внимание", "Выберите устройство")
        return

    filepath = filedialog.askopenfilename()
    if not filepath:
        return

    ip = devices[selection[0]][1]
    threading.Thread(target=send_file_to, args=(ip, filepath), daemon=True).start()

def send_all():
    filepath = filedialog.askopenfilename()
    if not filepath:
        return

    for _, ip in devices:
        threading.Thread(target=send_file_to, args=(ip, filepath), daemon=True).start()

send_button.config(command=send_selected)
send_all_button.config(command=send_all)

# ================= SETTINGS =================

def open_settings(event=None):
    global advanced_mode, TEACHER_IP

    advanced_mode = True
    send_all_button.grid(row=0, column=1, padx=5)
    update_device_list()

    settings = tk.Toplevel(root)
    settings.title("Настройки")
    settings.geometry("300x150")

    tk.Label(settings, text="IP учителя:").pack(pady=10)

    ip_entry = tk.Entry(settings)
    ip_entry.pack()
    ip_entry.insert(0, TEACHER_IP)

    def save_ip():
        new_ip = ip_entry.get().strip()
        if new_ip:
            config["teacher_ip"] = new_ip
            save_config(config)
            TEACHER_IP = new_ip
            discover_devices()
            settings.destroy()

    tk.Button(settings, text="Сохранить", command=save_ip).pack(pady=10)

root.bind("<Control-Shift-W>", open_settings)

# ================= SERVER FOLDER =================

def choose_folder():
    global save_folder
    folder = filedialog.askdirectory()
    if folder:
        save_folder = folder
        folder_label.config(text=f"Путь: {save_folder}")
        log(f"[✓] Новая папка: {save_folder}")

choose_button.config(command=choose_folder)

# ================= START =================

def main():
    log("=== INFOBOT 4.0 ===")
    log(f"Папка по умолчанию: {save_folder}")

    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_discovery, daemon=True).start()

    discover_devices()
    root.mainloop()

if __name__ == "__main__":
    main()
