import socket
import threading

def staring_connection(host,port):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((host,port))
    server_socket.listen(5)
    print(f"Server has started listening on port: {port} and on host: {host}")
    return server_socket

def new_client_join(canvas_history,lock_history,client_socket):
    with lock_history:
        snapshot = list(canvas_history)
    for points in snapshot:
        history_point = f"{points[1]}\n"
        new_point = history_point.encode('utf-8')
        client_socket.sendall(new_point)

def clear_command(canvas_history,lock_history,active_clients,client_socket):
    with lock_history:
        canvas_history.clear()
    for client in list(active_clients):
        if client != client_socket:
            client.sendall("CLEAR\n".encode('utf-8'))

def undo_command(canvas_history,lock_history,active_clients,client_socket):
    with lock_history:
        for points in reversed(canvas_history):
            if points[0] == client_socket:
                target_stroke_id = points[1].split(",")[1]
                break
        canvas_history[:] = [p for p in canvas_history if
                             not (p[0] == client_socket and p[1].split(",")[1] == target_stroke_id)]
    for client in list(active_clients):
        client.sendall("CLEAR\n".encode('utf-8'))
    with lock_history:
        snapshot = list(canvas_history)
    for client in list(active_clients):
        for points in snapshot:
            history_point = f"{points[1]}\n"
            new_point = history_point.encode('utf-8')
            client.sendall(new_point)

def cursor_command(line,active_clients,client_socket):
    for clients in list(active_clients):
        if clients != client_socket:
            clients.sendall(f"{line}\n".encode('utf-8'))

def normal_command(canvas_history,lock_history,active_clients,client_socket,client_colors,line):
    my_color = client_colors[client_socket]
    line_with_color = f"{my_color},{line}"
    with lock_history:
        canvas_history.append((client_socket, line_with_color))
    for client in list(active_clients):
        if client != client_socket:
            msg_to = (line_with_color + "\n").encode('utf-8')
            client.sendall(msg_to)

def save_command(canvas_history,lock_history):
    test_canvas_history = {}
    with lock_history:
        test_canvas_history = list(canvas_history)
    with open("whiteboard.txt","w",encoding='utf-8') as plik:
        for points in test_canvas_history:
            plik.write(f"{points[1]}\n")

def load_command(canvas_history, lock_history, active_clients):
    with open("whiteboard.txt","r",encoding='utf-8') as plik:
        lines = plik.readlines()
    prepared_lines = []
    for line in lines:
        prepared_lines.append((None,line.strip()))
    with lock_history:
        canvas_history.clear()
        canvas_history.extend(prepared_lines)
        snapshot = list(canvas_history)
    for clients in list(active_clients):
        clients.sendall("CLEAR\n".encode('utf-8'))
    for clients in list(active_clients):
        for points in snapshot:
            clients.sendall(f"{points[1]}\n".encode('utf-8'))

def client_handler(client_socket,active_clients,canvas_history,lock_history,client_colors):
    buffor = ""
    try:
        new_client_join(canvas_history,lock_history,client_socket)
        while True:
            msg_from = client_socket.recv(1024).decode('utf-8')
            if not msg_from:
                break
            buffor += msg_from
            while '\n' in buffor:
                line,buffor = buffor.split("\n",1)
                if line == "CLEAR":
                    clear_command(canvas_history,lock_history,active_clients,client_socket)
                elif line == "UNDO":
                    undo_command(canvas_history,lock_history,active_clients,client_socket)
                elif line.startswith("CURSOR,"):
                    cursor_command(line,active_clients,client_socket)
                elif line == "SAVE":
                    save_command(canvas_history,lock_history)
                elif line == "LOAD":
                    load_command(canvas_history,lock_history,active_clients)
                else:
                    normal_command(canvas_history,lock_history,active_clients,client_socket,client_colors,line)
    except ConnectionResetError:
        active_clients.remove(client_socket)
        client_socket.close()
        print("Client has suddenly left!")
    if client_socket in active_clients:
        active_clients.remove(client_socket)
        client_socket.close()
        print("Connection has been succesfully terminated")

def server_listening(canvas_history, lock_history, active_clients,server_socket,client_colors,COLORS):
    while True:
        client_socket , client_adress = server_socket.accept()
        active_clients.append(client_socket)
        client_colors[client_socket] = COLORS[(len(active_clients)%len(COLORS))]
        assigned_color = client_colors[client_socket]
        color_msg = f"MY_COLOR,{assigned_color}\n"
        client_socket.sendall(color_msg.encode('utf-8'))
        print(f"Client has connected on socket: {client_socket} and on adress: {client_adress}")
        threading.Thread(target=client_handler, args=(client_socket,active_clients,canvas_history,lock_history,client_colors), daemon=True).start()

def server_mechanic():
    COLORS = ["red","blue","green","purple","orange"]
    client_colors = {}
    active_clients = []
    canvas_history = []
    #Lock protecting canvas_history in all related fields
    lock_history = threading.Lock()
    server_socket = staring_connection('0.0.0.0',8888)
    server_listening(canvas_history,lock_history,active_clients,server_socket,client_colors,COLORS)

if __name__ == "__main__":
    server_mechanic()
