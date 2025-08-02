import socket
import selectors
from register_user import authenticate_user, register_user
import setup_DB

sel = selectors.DefaultSelector()
clients = {}


def accept_connection(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    clients[conn] = {"addr": addr, "name": None, "auth": None}
    print(f"Connected with {addr}")
    sel.register(conn, selectors.EVENT_READ, read_client)


def command_parser(command_data, client_sock):
    token = command_data.split()
    command = token[0].lower()
    args = token[1:]

    if command == "/pvt":
        if len(args) < 2:
            client_sock.send(b"Try Again: /pvt [name] [msg]")
            return

        reciepent_name = args[0]
        message = " ".join(args[1:])

        if reciepent_name == clients[client_sock]["name"]:
            client_sock.send(
                "ERROR!!: You cant sent private message To yourself".encode()
            )
            return

        for client in clients:
            if clients[client]["name"] == reciepent_name:
                sender = clients[client_sock].get("name")
                formatted_msg = f"[Private] {
                    sender.title()}: {message}".encode()
                client.send(formatted_msg)
                client_sock.send(b"[Private message sent]\n")
                return

        client_sock.send(b"[!] User not found.\n")

    elif command == "/who":
        if len(clients) == 1:
            client_sock.send("No One is connected Yet")
            return

        for client in clients:
            if client != client_sock:
                client_sock.send(clients[client]["name"].encode())

    elif command == "/rename":
        #
        if len(args) < 1:
            client_sock.send(b"Try Again: /rename <new_username> ")
            return

        clients[client_sock]["name"] = args[0]

        client_sock.send(f"__new_username__ {args[0]}".encode())

    elif command == "/whoami":
        client_sock.send(
            f"      User address(ip_addr, port_number) :: {
                clients[client_sock]['addr']
            }\n".encode()
        )
        client_sock.send(f"      Username :: {
                         clients[client_sock]['name']}".encode())
    elif command == "/exit":
        client_sock.send(b"__EXIT__")

    elif command == "/help":
        help_msg = """
        Available commands:
        /who              - List connected users
        /pvt <user> <msg> - Send private message
        /rename <new>     - Change your username
        /exit             - Leave the chat
        """
        client_sock.send(help_msg.encode())

    else:
        client_sock.send(f"💣 Unkown command {command}".encode())


def read_client(conn):
    try:
        data = conn.recv(1024)
        if data:
            # first data will be of authentication or Registration
            # this  will only when  there is the first time Registration

            if not clients[conn]["auth"]:
                username, password, option = data.decode().split("::")

                if option == "1":
                    if register_user(username, password):
                        conn.send(b"[+] Registration successful.")
                        clients[conn]["name"] = username
                        clients[conn]["auth"] = True
                    else:
                        conn.send(
                            b"[-] Username already exists. Try again with Different one"
                        )
                    return

                else:  # this will be for the authentication
                    if authenticate_user(username, password):
                        conn.send(b"[+] Login successful.")
                        clients[conn]["name"] = username
                        clients[conn]["auth"] = True

                    else:
                        conn.send(b"[-] Login unsuccessful")
                    return

            if data.decode().strip().startswith("/"):
                command_parser(data.decode().strip(), conn)
                return

            if len(clients) <= 1:
                conn.send(b"No other clients are Connected")
                return
            else:
                for client in clients:
                    if client != conn:
                        try:
                            sender = clients[conn].get("name")
                            # this ANSI color code , helps in making nice colored username, i just get to know from my friend
                            formatted_msg = f"{sender}: {
                                data.decode()}".encode()
                            client.send(formatted_msg)

                        except Exception as e:
                            print(f"Failed to send {e}")
        else:
            # client is disconnected, when there is no data, means we are not getting any bytes that is what is
            print(f"Client {clients[conn]} is disconnected")
            sel.unregister(conn)
            conn.close()
            del clients[conn]

    except ConnectionResetError:
        # any error occurred
        print(f"Client {clients[conn]} is forcefully disconnected")
        sel.unregister(conn)
        conn.close()
        del clients[conn]


# Setup
server = socket.socket()
# 0.0.0.0 is the universal connector , means you can connect to this server
server.bind(("0.0.0.0", 5000))
# using any means of connection either localhost or through the ip address and all
server.listen()
server.setblocking(False)

sel.register(server, selectors.EVENT_READ, accept_connection)

print("Chat Server is running..... ")

# Event loop
#
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
