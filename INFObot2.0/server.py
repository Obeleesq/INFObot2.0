import socket
import threading
import os
from pathlib import Path
import platform

TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 4096

# Имя ноутбука автоматически
SERVER_NAME = platform.node()

downloads_folder = str(Path.home() / "Downloads")


# ===================== TCP СЕРВЕР (приём файлов) =====================

def handle_client(conn, addr):
    try:
        # Получаем размер имени файла (4 байта)
        name_size_bytes = conn.recv(4)
        if not name_size_bytes:
            return

        name_size = int.from_bytes(name_size_bytes, 'big')

        # Получаем имя файла
        filename = conn.recv(name_size).decode('utf-8')

        filepath = os.path.join(downloads_folder, filename)

        with open(filepath, "wb") as f:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

        print(f"[✓] Получен файл: {filename} от {addr}")

    except Exception as e:
        print("Ошибка при получении файла:", e)

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


# ===================== UDP DISCOVERY =====================

def udp_discovery():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", UDP_PORT))

    print(f"[UDP] Discovery активен на порту {UDP_PORT}")

    while True:
        data, addr = udp.recvfrom(1024)

        if data.decode() == "DISCOVER_INFOBOT":
            response = f"INFOBOT|{SERVER_NAME}"
            udp.sendto(response.encode(), addr)


# ===================== ЗАПУСК =====================

if __name__ == "__main__":
    print("=== INFOBOT SERVER 2.0 ===")

    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_discovery, daemon=True).start()

    # Держим программу живой
    while True:
        pass
