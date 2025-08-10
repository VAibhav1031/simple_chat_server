import socket
import selectors
from register_user import authenticate_user, register_user
import setup_DB

sel = selectors.DefaultSelector()
clients = {}
rooms = {}  # room_name -> list of sockets


def accept_connection(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    clients[conn] = {
        "addr": addr,
        "name": None,
        "auth": None,
        "room": None,
        "in_room_mode": False,
    }
    print(f"Connected with {addr}")
    sel.register(conn, selectors.EVENT_READ, read_client)


# ---------------------------COMMAND-PARSER-ESSENTIALS----------------------------
def handle_pvt(client_sock, args):
    if len(args) < 2:
        client_sock.send(b"Try Again: /pvt [name] [msg]")
        return

    reciepent_name = args[0]
    message = " ".join(args[1:])

    if reciepent_name == clients[client_sock]["name"]:
        client_sock.send("ERROR!!: You cant sent private message To yourself".encode())
        return

    for client in clients:
        if (
            clients[client]["name"] == reciepent_name
            and not clients[client]["in_room_mode"]
        ):
            sender = clients[client_sock].get("name")
            formatted_msg = f"[Private] {sender.title()}: {message}".encode()
            client.send(formatted_msg)
            client_sock.send(b"[Private message sent]\n")
            return

    client_sock.send(b"[!] User not found.\n")


def handle_who(client_sock):
    if len(clients) == 1:
        client_sock.send(b"No One is connected Yet")
        return

    names = [clients[c]["name"] for c in clients if c != client_sock]
    client_sock.send("\n".join(names).encode())


def handle_whoami(client_sock):
    info = clients[client_sock]
    msg = f"User address :: {info['addr']}\nUsername :: {info['name']}"
    client_sock.send(msg.encode())


def handle_rename(client_sock, args):
    #
    if len(args) < 1:
        client_sock.send(b"Try Again: /rename <new_username> ")
        return

    clients[client_sock]["name"] = args[0]

    client_sock.send(f"__new_username__ {args[0]}".encode())


def handle_help(client_sock):
    help_msg = """
    Available commands:
    /who              - List connected users
    /pvt <user> <msg> - Send private message
    /rename <new>     - Change your username
    /whoami           - About yourself
    /room             - Enter room session
    /ping             - ping the server
    /exit             - Leave the chat
    """
    client_sock.send(help_msg.encode())


def handle_help_room(client_sock):
    help_msg = """
    [ Room Mode Commands ]
    /leave_room         - Exit room session and return to global chat
    /room_create <name> - Create a new room
    /room_join <name>   - Join an existing room
    /leave_current_room - Leave the room you are currently in (stay in room mode)
    /room_help          - Show this help menu

    Notes:
    - While in room mode, your messages go only to members of your current room.
    - If you are in room mode but not in any room, you must /room_join or /room_create before sending messages.
"""
    client_sock.send(help_msg.encode())


# ------------------------------------------------XXXXXX----------------------------------


# ----------------------------------------room-------------------------------------------
def create_room(client_sock, room_name):
    if room_name in rooms:
        client_sock.send(b"[!] Room already exists.")
        return
    rooms[room_name] = set()
    client_sock.send(f"[+] Room '{room_name}' created".encode())


def join_room(client_sock, room_name):
    if room_name not in rooms:
        client_sock.send(b"[!] Room does not exist.")
        return

    leave_current_room(client_sock)
    rooms[room_name].add(client_sock)
    clients[client_sock]["room"] = room_name
    client_sock.send(f"[+] Joined room '{room_name}'.".encode())


def leave_current_room(client_sock):
    current_room = clients[client_sock].get("room")
    if current_room and current_room in rooms:
        rooms[current_room].discard(client_sock)
    clients[client_sock]["room"] = None
    client_sock.send(b"[+] Left the room.")


def send_room_message(client_sock, message):
    room_name = clients[client_sock].get("room")
    if not clients[client_sock]["room"]:
        client_sock.send(b"[!] Join or create a room first.")
        return

    sender = clients[client_sock]["name"]
    for member in rooms[room_name]:
        if member != client_sock:
            member.send(f"[{room_name}] {sender}: {message}".encode())


# --------------------------------------------------------------------------------------------


def global_handler(command_data, client_sock):
    token = command_data.strip().split()
    if not token:
        return

    command, args = token[0].lower(), token[1:]

    command_map = {
        "/pvt": lambda: handle_pvt(client_sock, args),
        "/who": lambda: handle_who(client_sock),
        "/rename": lambda: handle_rename(client_sock, args),
        "/whoami": lambda: handle_whoami(client_sock),
        "/exit": lambda: client_sock.send(b"__EXIT__"),
        "/ping": lambda: client_sock.send("Pong 🏓 Recieved!!".encode()),
        "/help": lambda: handle_help(client_sock),
    }
    handler = command_map.get(command)
    if handler:
        handler()
    else:
        client_sock.send(f"❓Unkown command : {command}".encode())


def command_parser(data, conn):
    if clients[conn]["in_room_mode"]:
        room_handler(conn, data)
    else:
        global_handler(data, conn)


def enter_room_mode(conn):
    if clients[conn]["in_room_mode"]:
        conn.send(b"Room session already created !!.")
        return
    clients[conn]["in_room_mode"] = True
    clients[conn]["room"] = None
    conn.send(b"Entered room mode. Type /room_help for options.")


def room_handler(client_sock, data):
    token = data.strip().split()
    if not token:
        return

    cmd, args = token[0].lower(), token[1:]

    if cmd == "/room_create":
        if not args:
            client_sock.send(b"Usage: /room_create <name>")
            return
        create_room(client_sock, args[0])

    elif cmd == "/leave_current_room":
        leave_current_room(client_sock)

    elif cmd == "/room_join":
        if not args:
            client_sock.send(b"Usage: /room_join <name>")
            return
        join_room(client_sock, args[0])

    elif cmd == "/room_help":
        handle_help_room(client_sock)

    else:
        client_sock.send(f"❓Unkown command : {cmd}".encode())


def auth_solver(conn, data):
    try:
        username, password, option = data.decode().split("::", 2)

        if option == "1":
            if register_user(username, password):
                conn.send(b"[+] Registration successful.")
                clients[conn]["name"] = username
                clients[conn]["auth"] = True
            else:
                conn.send(b"[-] Username already exists. Try again with Different one")
            return

        else:  # this will be for the authentication
            if authenticate_user(username, password):
                conn.send(b"[+] Login successful.")
                clients[conn]["name"] = username
                clients[conn]["auth"] = True

            else:
                conn.send(b"[-] Login unsuccessful")
            return

    except Exception as e:
        print(f"[Auth Error] {e}")


def room_exit_entry(client_sock, cmd):
    if cmd == "/room":
        enter_room_mode(client_sock)
        return True

    if cmd == "/leave_room":
        clients[client_sock]["in_room_mode"] = False
        clients[client_sock]["room"] = None
        client_sock.send(b"Exited room mode.")
        return True

    return False


def broadcast_global(sender_sock, message):
    if len(clients) <= 1:
        sender_sock.send(b"No other clients are connected.")
        return

    sender_name = clients[sender_sock]["name"]
    for client in clients:
        if client != sender_sock and not clients[client]["in_room_mode"]:
            client.send(f"{sender_name}: {message}".encode())


def disconnect_client(conn):
    print(f"\nClient {clients[conn]} is disconnected")
    sel.unregister(conn)
    conn.close()
    del clients[conn]


def read_client(conn):
    try:
        raw_data = conn.recv(1024)
        if not raw_data:
            disconnect_client(conn)
            return

        text = raw_data.decode().strip()

        # Step 1: Authentication
        if not clients[conn]["auth"]:
            auth_solver(conn, raw_data)
            return

        # Step 2: Room session enter/exit
        if room_exit_entry(conn, text):
            return

        # Step 3: Commands
        if text.startswith("/"):
            command_parser(text, conn)
            return

        # Step 4: Messages
        if clients[conn]["in_room_mode"]:
            send_room_message(conn, text)
        else:
            broadcast_global(conn, text)

    except ConnectionResetError:
        disconnect_client(conn)


# Setup
server = socket.socket()

# 0.0.0.0 is the universal connector , means you can connect to this server
server.bind(("0.0.0.0", 5000))
# using any means of connection either localhost or through the ip address and all


server.listen()  # You are server is nowwww readddy broooo
server.setblocking(
    False
)  # since you are using chat server we may get connection or send recv thing at nearly same time , to stop
# the block  period from the send recv and other utilities we block---> false

sel.register(server, selectors.EVENT_READ, accept_connection)

print("Chat Server is running..... ")

# Event loop
try:
    while True:
        events = sel.select()
        print(events)
        for key, _ in events:
            callback = key.data
            callback(key.fileobj)

except KeyboardInterrupt:
    print("\nShutting down the server")

finally:
    sel.close()
    server.close()
# Now when data is ready (event happens):

# You get an event list like this:

# events = sel.select()
# Each key in events is a SelectorKey object with:
# Attribute	Meaning
# key.fileobj	The socket or file object that is ready (e.g., a client socket).
# key.data	Whatever data you attached during sel.register(...) (here: the callback_function).

# So:

# callback = key.data
# callback(key.fileobj)
#
# Means:
#
#     “Call the function I registered, passing the ready socket to it.”
#
#  Analogy


# Think of selectors as a receptionist:
#
#     You tell them: “Let me know when this socket has data to read.”
#
#     And: “When it’s ready, call this function with that socket.”
#
# The key.data is that function.
# The key.fileobj is the socket that’s ready.
# Example for Clarity
#
# def handle_client(sock):
#     data = sock.recv(1024)
#     print("Received:", data.decode())
#
# sel.register(client_socket, selectors.EVENT_READ, handle_client)
#
# Now when client_socket is readable:
#
#     key.fileobj is client_socket
#
#     key.data is handle_client
#
#     So: handle_client(client_socket) gets called.
#
#  So, the while True loop:
#
# while True:
#     events = sel.select()
#     for key, _ in events:
#         callback = key.data
#         callback(key.fileobj)
#
# Keeps checking for ready sockets
# Calls the correct callback handler when they're ready
# Passes the specific socket that needs handling
