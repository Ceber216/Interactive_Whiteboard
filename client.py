import socket
import threading
import tkinter

def setup():
    socket_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socket_server.connect(('127.0.0.1',8888))
    return socket_server


def receive_messanges(client_socket,canvas,my_color):
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
                    elif line:
                        coords = line.split(',')
                        if len(coords) == 6:
                            try:
                                x1, y1, x2, y2 = map(int, coords[2:])
                                canvas.create_line(x1, y1, x2, y2, fill=coords[0], width=2)
                            except ValueError:
                                continue

    except ConnectionResetError:
        print("Connection terminated")
    client_socket.close()

def save_position(event,mouse_pos,stroke):
    mouse_pos['x'] = event.x
    mouse_pos['y'] = event.y
    stroke[0] += 1

def draw_and_send(event,mouse_pos,canvas,my_socket,stroke,my_color):
    last_x = mouse_pos['x']
    last_y = mouse_pos['y']
    if last_x is not None and last_y is not None:
        canvas.create_line(last_x,last_y,event.x,event.y,fill = my_color[0], width = 2)
        msg = f"{stroke[0]},{last_x},{last_y},{event.x},{event.y}\n"
        my_socket.sendall(msg.encode('utf-8'))
    mouse_pos['x'] = event.x
    mouse_pos['y'] = event.y

def clear_all(my_socket,canvas):
    canvas.delete("all")
    my_socket.sendall("CLEAR\n".encode('utf-8'))

def undo_previous(my_socket):
    my_socket.sendall("UNDO\n".encode('utf-8'))

def client_main():
    mouse_pos = {'x': None, 'y': None}
    my_color = ["black"]
    stroke = [0]
    my_socket = setup()
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root,width=800,height=600,bg = 'white')
    canvas.pack()
    canvas.focus_set()
    threading.Thread(target=receive_messanges, args=(my_socket, canvas,my_color), daemon=True).start()
    canvas.bind("<Button-1>",lambda e: save_position(e,mouse_pos,stroke))
    canvas.bind("<B1-Motion>",lambda e: draw_and_send(e,mouse_pos,canvas,my_socket,stroke,my_color))
    canvas.bind("<c>",lambda e: clear_all(my_socket,canvas))
    canvas.bind("<z>",lambda e: undo_previous(my_socket))
    root.mainloop()
if __name__ == "__main__":
    client_main()