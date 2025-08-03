import socket
import threading
import sys
import time
# i will explain you  what is  the  threading.Event()
# it is special type of  bool,  with lot of attributes

# threading.Event is a synchronization primitive.
#
# You can think of it as an advanced bool, but with internal logic that supports:
#     blocking with .wait()
#     thread-safe setting/clearing
#     notification to waiting threads

# meaning it has lot of feature rather than normal bool which is  only for the  set and not set , which
# doesnt give allround effect in threading like  environment where maybe more than one thread could be running


# 🔹 How .wait() works (under the hood)
#
# When you call:
#
# exit_flag = threading.Event()
# exit_flag.wait()
#
#     The calling thread blocks (sleeps) until some other thread calls exit_flag.set().
#
#     Under the hood, it uses:
#
#         A lock to ensure thread-safe updates.
#         A condition variable to sleep and wake threads efficiently.
#
# So, .wait() does not busy-wait, it blocks the thread efficiently (no CPU usage while sleeping).
#
# This is different from while not my_bool: pass which wastes CPU.


# Important ::
# hy Event() is ideal for signaling
#
# When you want to signal between threads — like:
#
#     tell workers to stop
#
#     notify another thread to continue
#
#     coordinate between loops
#
# → Event() is cleaner, safer, and OS-optimized.
# ---------------------------------------------------------------------------------------------


# #  First i went for the ASCII using the pyfiglet, then i thought about the
# # SOme thing better, you must all go with this site "http://patorjk.com/software/taag/"
banner_textttu = """

             ██████  ██   ██  █████  ████████     ███████ ███████ ██████  ██    ██ ███████ ██████
            ██       ██   ██ ██   ██    ██        ██      ██      ██   ██ ██    ██ ██      ██   ██
            ██       ███████ ███████    ██        ███████ █████   ██████  ██    ██ █████   ██████
            ██       ██   ██ ██   ██    ██             ██ ██      ██   ██  ██  ██  ██      ██   ██
             ██████  ██   ██ ██   ██    ██        ███████ ███████ ██   ██   ████   ███████ ██   ██


                                 S I M P L E   C H A T   S E R V E R
            ---------------------------------------------------------------------------------------
                                    ▖ ▖         ▖  ▖▄▖
               by  -->              ▛▖▌█▌▛▘▛▘▛▌ ▛▖▞▌▌▌▛▌▛▘█▌▛▘
                                    ▌▝▌▙▖▙▖▌ ▙▌ ▌▝ ▌▛▌▌▌▙▖▙▖▌
            ---------------------------------------------------------------------------------------
    """

print("\033[38;5;197m" + banner_textttu + "\033[0m")

exit_flag = threading.Event()
auth_needed_flag = threading.Event()
user_name_holder = [None]
AUTH_REGISTER = "2"
AUTH_LOGIN = "1"
start_time = None
end_time = None


def send_msg(sock, msg):
    try:
        sock.send(msg.encode())
    except:
        pass


def auth_setup(sock):
    print("\033[38;5;230m 1. Register (New User 👶) \033[0m")
    print("\033[38;5;230m 2. Enter (Old User 🧓) \033[0m")

    option_ = input("\n\033[38;5;205m Enter the option(1 or 2) : \033[0m")
    user_name = None
    password = None
    while not user_name or not password:
        user_name = input("\033[38;5;230m Enter your username: \033[0m ")
        password = input("\033[38;5;230m Enter the password: \033[0m ")

    user_name_holder[0] = user_name

    if option_ == AUTH_LOGIN:
        msg = f"{user_name}::{password}::{AUTH_LOGIN}"
        send_msg(sock, msg)

    else:
        msg = f"{user_name}::{password}::{AUTH_REGISTER}"
        send_msg(sock, msg)

    time.sleep(1.5)
    print("\n\n\033[38;5;226m [-]Connecting ....\033[0m")
    time.sleep(0.8)
    print("\n\033[38;5;226m [-]Wait bro ~~~~!!!!~~~ \033[0m")
    time.sleep(1.2)
    print("\n\033[38;5;226m ⏰...\033[0m")
    time.sleep(1)
    print("""\n\033[38;5;226m [✓] Connected to server[!]\033[0m\n\n""")
    print(
        """\n\033[38;5;226m---------------------------------------------------------\033[0m\n"""
    )
    time.sleep(1)


def receive_messages(sock):
    while not exit_flag.is_set():
        try:
            data = sock.recv(1048)
            if not data:
                print("\n[!]💣 Server disconnected.")
                exit_flag.set()
                break

            msssg = data.decode()
            if msssg.startswith("Pong"):
                end_time = time.time()
                print(
                    f"\033[38;5;83m[Server]: 🏓PONG received ({
                        (end_time - start_time) * 100
                    }ms)!\033[0m"
                )

            if msssg.startswith("__new_username__"):
                user_name_holder[0] = data.decode().split()[1]
                continue

            if msssg.startswith("__EXIT__"):
                send_msg(sock, "⛔ HAS LEFT THE CHAT .")
                sys.stdout.write("\r" + " " * 100 + "\r")
                exit_flag.set()
                break
            sys.stdout.write("\r" + " " * 100 + "\r")
            print(f"\033[38;5;46m{data.decode()}\033[0m")
            if msssg.startswith("[-]"):
                auth_needed_flag.set()
                exit_flag.set()
                break

            sys.stdout.write(f"\033[38;5;51m{user_name_holder[0]}\033[0m :")
            sys.stdout.flush()

        except (ConnectionResetError, OSError) as e:
            print(f"\n[!] Connection error: {e}")
            exit_flag.set()
            break


def setup_socket():
    # the socket is setup for the TCP protocol with IPV4
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

    try:
        sock.connect((server_ip, 5000))
    except Exception as e:
        print(f"[!] Could not connect to server: {e}")
        sys.exit(1)

    return sock


def start_recv_thread(sock):
    recv_thread = threading.Thread(target=receive_messages, args=(sock,))
    # recv_thread.daemon = True
    recv_thread.start()
    return recv_thread


def handle_input(sock):
    try:
        while not exit_flag.is_set():
            msg = input(f"\033[38;5;51m{user_name_holder[0]}\033[0m :")
            if msg.strip().lower() == "/ping":
                global start_time
                start_time = time.time()
                send_msg(sock, f"{msg}")
            if exit_flag.is_set():
                break
            elif msg.strip():
                send_msg(sock, f"{msg}")

    except (KeyboardInterrupt, EOFError):
        print("\n[!] Exiting chat...")


def main():
    while True:
        client_sock = setup_socket()
        auth_setup(client_sock)
        recv_thread = start_recv_thread(client_sock)

        while not exit_flag.is_set():
            handle_input(client_sock)

        recv_thread.join()
        client_sock.close()

        if not auth_needed_flag.is_set():
            break
        else:
            auth_needed_flag.clear()
            exit_flag.clear()


if __name__ == "__main__":
    main()
# current we are going with the exit to exit the chat not something like
# /quit /pvt (like a direct dm to a person no to whole group oka )


# so the confusion is gone, mann, in receive() function there is
# one more  important part is going , which is like
# whenever there is main thread is running  it is taking the input  continousuly ,
# but at same moment when the data is came from the other connected people
# So to make it more better looking the current line is cleared (Whcih is input promt ), so the text of that is cleared and
# the message is printed,  so to make the continous flow , we use to print the cleared text during the printing of the message
# that is only one thing nothing else
