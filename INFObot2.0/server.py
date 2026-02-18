import socket
import threading
import os
from pathlib import Path
import platform

TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 4096

SERVER_NAME = platform.node()
downloads_folder = str(Path.home() / "Downloads")
os.makedirs(downloads_folder, exist_ok=True)

print("Файлы сохраняются в:", downloads_folder)

# ================= TCP =================

def handle_client(conn, addr):
    try:
        print("Подключение от:", addr)

        # Получаем ровно 4 байта длины имени
        name_size_bytes = b""
        while len(name_size_bytes) < 4:
            chunk = conn.recv(4 - len(name_size_bytes))
            if not chunk:
                print("Не удалось получить размер имени")
                return
            name_size_bytes += chunk

        name_size = int.from_bytes(name_size_bytes, 'big')

        # Получаем имя файла
        filename_bytes = b""
        while len(filename_bytes) < name_size:
            chunk = conn.recv(name_size - len(filename_bytes))
            if not chunk:
                print("Ошибка при получении имени")
                return
            filename_bytes += chunk

        filename = filename_bytes.decode("utf-8")
        filename = os.path.basename(filename)

        filepath = os.path.join(downloads_folder, filename)
        print("Сохраняю:", filepath)

        # Принимаем файл
        with open(filepath, "wb") as f:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

        print("[✓] Файл успешно получен")

    except Exception as e:
        print("Ошибка:", e)

    finally:
        conn.close()


def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", TCP_PORT))
    server.listen(5)
    print(f"[TCP] Сервер запущен на порту {TCP_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# ================= UDP DISCOVERY =================

def udp_discovery():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", UDP_PORT))
    print(f"[UDP] Discovery активен на порту {UDP_PORT}")

    while True:
        data, addr = udp.recvfrom(1024)
        if data.decode() == "DISCOVER_SERVER":
            udp.sendto(b"SERVER_HERE", addr)


# ================= ЗАПУСК =================

if __name__ == "__main__":
    print("=== INFOBOT SERVER 2.0 ===")
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_discovery, daemon=True).start()

    while True:
        pass
