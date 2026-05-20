import socket
import threading
import tkinter
from tkinter import simpledialog


def setup():
    socket_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socket_server.connect(('127.0.0.1',8888))
    return socket_server

def cursor_mechanic(canvas,remote_cursor,line):
    parts = line.split(',')
    if len(parts) == 4:
        client_name = parts[1]
        if client_name in remote_cursor:
            old_oval, old_text = remote_cursor[client_name]
            canvas.delete(old_oval)
            canvas.delete(old_text)
        new_oval = canvas.create_oval(int(parts[2]) - 4, int(parts[3]) - 4, int(parts[2]) + 4, int(parts[3]) + 4,
                                      fill="red")
        new_text = canvas.create_text(int(parts[2]), int(parts[3]) - 12, text=client_name, fill="black",
                                      font=("Arial", 9))
        remote_cursor[client_name] = new_oval, new_text

def create_line(canvas,line):
    coords = line.split(',')
    if len(coords) == 7:
        try:
            x1, y1, x2, y2 = map(int, coords[3:])
            canvas.create_line(x1, y1, x2, y2, fill=coords[0], width=int(coords[2]), capstyle="round")
        except ValueError:
            return

def receive_messages(client_socket,canvas,my_color,remote_cursor):
    buffor = ""
    try:
        while True:
            msg = client_socket.recv(1024).decode('utf-8')
            if not msg:
                break
            buffor += msg
            while '\n' in buffor:
                line,buffor = buffor.split("\n",1)
                if line:
                    if line == "CLEAR":
                        canvas.delete("all")
                    elif line.startswith("MY_COLOR",):
                        my_color[0] = line.split(",")[1]
                    elif line.startswith("CURSOR,"):
                        cursor_mechanic(canvas,remote_cursor,line)
                    elif line:
                        create_line(canvas,line)

    except ConnectionResetError:
        print("Connection terminated")
    client_socket.close()

def save_position(event,mouse_pos,stroke):
    mouse_pos['x'] = event.x
    mouse_pos['y'] = event.y
    stroke[0] += 1

def draw_and_send(event,mouse_pos,canvas,my_socket,stroke,my_color,gauge):
    actual_number = gauge.get()
    last_x = mouse_pos['x']
    last_y = mouse_pos['y']
    if last_x is not None and last_y is not None:
        canvas.create_line(last_x,last_y,event.x,event.y,fill = my_color[0], width = actual_number,capstyle="round")
        msg = f"{stroke[0]},{actual_number},{last_x},{last_y},{event.x},{event.y}\n"
        my_socket.sendall(msg.encode('utf-8'))
    mouse_pos['x'] = event.x
    mouse_pos['y'] = event.y

def send_cursor(event,name,my_socket):
    my_socket.sendall(f"CURSOR,{name},{event.x},{event.y}\n".encode('utf-8'))

def clear_all(my_socket,canvas):
    canvas.delete("all")
    my_socket.sendall("CLEAR\n".encode('utf-8'))

def undo_previous(my_socket):
    my_socket.sendall("UNDO\n".encode('utf-8'))

def canvas_mechanic(root,my_socket,my_color,remote_cursor,mouse_pos,stroke,name):
    gauge = tkinter.IntVar(value=2)
    canvas = tkinter.Canvas(root, width=800, height=600, bg='white')
    slider = tkinter.Scale(root, from_=1, to=20, orient='horizontal', resolution=1, variable=gauge)
    canvas.pack()
    slider.pack()
    canvas.focus_set()
    threading.Thread(target=receive_messages, args=(my_socket, canvas, my_color, remote_cursor), daemon=True).start()
    canvas.bind("<Button-1>", lambda e: save_position(e, mouse_pos, stroke))
    canvas.bind("<B1-Motion>", lambda e: draw_and_send(e, mouse_pos, canvas, my_socket, stroke, my_color, gauge))
    canvas.bind("<Motion>", lambda e: send_cursor(e, name, my_socket))
    canvas.bind("<c>", lambda e: clear_all(my_socket, canvas))
    canvas.bind("<z>", lambda e: undo_previous(my_socket))
    root.mainloop()

def client_main():
    root = tkinter.Tk()
    name = simpledialog.askstring("Create your name","Write your name here:",initialvalue="Anonim")
    remote_cursor = {}
    mouse_pos = {'x': None, 'y': None}
    my_color = ["black"]
    stroke = [0]
    my_socket = setup()
    canvas_mechanic(root,my_socket,my_color,remote_cursor,mouse_pos,stroke,name)
if __name__ == "__main__":
    client_main()