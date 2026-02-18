import socket
import tkinter as tk
from tkinter import filedialog
import os

TEACHER_IP = "172.20.10.14"
TCP_PORT = 5001
BUFFER_SIZE = 4096

# ================= ОТПРАВКА =================

def send_file_to_target(target_ip, file_path):
    filename = os.path.basename(file_path)
    filename_bytes = filename.encode("utf-8")
    name_size = len(filename_bytes)

    try:
        s = socket.socket()
        s.connect((target_ip, TCP_PORT))

        # Отправляем длину имени (4 байта)
        s.send(name_size.to_bytes(4, 'big'))

        # Отправляем имя
        s.send(filename_bytes)

        # Отправляем файл
        with open(file_path, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                s.sendall(data)

        s.close()
        print("[✓] Файл отправлен")

    except Exception as e:
        print("Ошибка отправки:", e)


def choose_and_send():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    send_file_to_target(TEACHER_IP, file_path)


# ================= GUI =================

root = tk.Tk()
root.title("INFObot 2.0")
root.geometry("400x200")

btn = tk.Button(root, text="Отправить файл", font=("Arial", 14), command=choose_and_send)
btn.pack(expand=True)

root.mainloop()
