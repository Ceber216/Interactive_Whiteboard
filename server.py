import socket
import threading

def staring_connection(host,port):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((host,port))
    server_socket.listen(5)
    print(f"Server has started listening on port: {port} and on host: {host}")
    return server_socket


def client_handler(client_socket,active_clients,canvas_history,lock_history,client_colors):
    buffor = ""
    try:
        with lock_history:
            snapshot = list(canvas_history)
        for points in snapshot:
            history_point = f"{points[1]}\n"
            new_point = history_point.encode('utf-8')
            client_socket.sendall(new_point)
        while True:
            msg_from = client_socket.recv(1024).decode('utf-8')
            if not msg_from:
                break
            buffor += msg_from
            while '\n' in buffor:
                line,buffor = buffor.split("\n",1)
                if line == "CLEAR":
                    with lock_history:
                        canvas_history.clear()
                    for client in active_clients:
                        if client != client_socket:
                            client.sendall("CLEAR\n".encode('utf-8'))
                elif line == "UNDO":
                    with lock_history:
                        for points in reversed(canvas_history):
                            if points[0] == client_socket:
                                target_stroke_id = points[1].split(",")[1]
                                break
                        canvas_history[:] = [p for p in canvas_history if not (p[0] == client_socket and p[1].split(",")[1] == target_stroke_id)]
                    for client in active_clients:
                        client.sendall("CLEAR\n".encode('utf-8'))
                    with lock_history:
                        snapshot = list(canvas_history)
                    for client in active_clients:
                        for points in snapshot:
                            history_point = f"{points[1]}\n"
                            new_point = history_point.encode('utf-8')
                            client.sendall(new_point)
                elif line.startswith("CURSOR,"):
                    for clients in active_clients:
                        if clients != client_socket:
                            clients.sendall(f"{line}\n".encode('utf-8'))
                else:
                    my_color = client_colors[client_socket]
                    line_with_color = f"{my_color},{line}"
                    with lock_history:
                        canvas_history.append((client_socket,line_with_color))
                    for client in active_clients:
                        if client != client_socket:
                            msg_to = (line_with_color + "\n").encode('utf-8')
                            client.sendall(msg_to)

    except ConnectionResetError:
        active_clients.remove(client_socket)
        client_socket.close()
        print("Client has suddenly left!")
    if client_socket in active_clients:
        active_clients.remove(client_socket)
        client_socket.close()
        print("Connection has been succesfully terminated")

def server_mechanic():
    COLORS = ["red","blue","green","purple","orange"]
    client_colors = {}
    active_clients = []
    canvas_history = []
    #Lock protecting canvas_history in all related fields
    lock_history = threading.Lock()
    server_socket = staring_connection('0.0.0.0',8888)
    while True:
        client_socket , client_adress = server_socket.accept()
        active_clients.append(client_socket)
        client_colors[client_socket] = COLORS[(len(active_clients)%len(COLORS))]
        assigned_color = client_colors[client_socket]
        color_msg = f"MY_COLOR,{assigned_color}\n"
        client_socket.sendall(color_msg.encode('utf-8'))
        print(f"Client has connected on socket: {client_socket} and on adress: {client_adress}")
        threading.Thread(target=client_handler, args=(client_socket,active_clients,canvas_history,lock_history,client_colors), daemon=True).start()

if __name__ == "__main__":
    server_mechanic()
