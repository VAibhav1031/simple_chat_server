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
print("""


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

    """)


exit_flag = threading.Event()
auth_needed_flag = threading.Event()
user_name_holder = [None]
AUTH_REGISTER = "2"
AUTH_LOGIN = "1"


def send_msg(sock, msg):
    try:
        sock.send(msg.encode())
    except:
        pass


def auth_setup():
    print("1. Enter (Old User 🧓)")
    print("2. Register New User 👶 ")

    option_ = input("\nEnter the option : ")
    user_name = None
    password = None
    while not user_name or not password:
        user_name = input("Enter your username: ")
        password = input("Enter the password: ")

    user_name_holder[0] = user_name

    if option_ == AUTH_LOGIN:
        msg = f"{user_name}::{password}::{AUTH_LOGIN}"
        send_msg(sock, msg)

    else:
        msg = f"{user_name}::{password}::{AUTH_REGISTER}"
        send_msg(sock, msg)

    time.sleep(1)
    print("""[✓] Connected to server[!]""")


def receive_messages(sock):
    while not exit_flag.is_set():
        try:
            data = sock.recv(1048)
            if not data:
                print("\n[!] Server disconnected.")
                exit_flag.set()
                break

            msssg = data.decode()
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


# the socket is setup for the TCP protocol with IPV4
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

try:
    sock.connect((server_ip, 5000))
except Exception as e:
    print(f"[!] Could not connect to server: {e}")
    sys.exit(1)

# we have to go with the ask to the user
# new use

####
auth_setup()
####


recv_thread = threading.Thread(target=receive_messages, args=(sock,))
recv_thread.start()


try:
    while not exit_flag.is_set():
        msg = input(f"\033[38;5;51m{user_name_holder[0]}\033[0m :")
        if exit_flag.is_set():
            break
        elif msg.strip():
            send_msg(sock, f"{msg}")


except (KeyboardInterrupt, EOFError):
    print("\n[!] Exiting chat...")

finally:
    exit_flag.set()
    sock.close()
    recv_thread.join()
    if auth_needed_flag.is_set():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

        try:
            sock.connect((server_ip, 5000))
        except Exception as e:
            print(f"[!] Could not connect to server: {e}")
            sys.exit(1)

        exit_flag.clear()
        auth_needed_flag.clear()
        auth_setup()

        recv_thread = threading.Thread(target=receive_messages, args=(sock,))
        recv_thread.start()
    # sys.exit(0)


# current we are going with the exit to exit the chat not something like
# /quit /pvt (like a direct dm to a person no to whole group oka )


# so the confusion is gone, mann, in receive() function there is
# one more  important part is going , which is like
# whenever there is main thread is running  it is taking the input  continousuly ,
# but at same moment when the data is came from the other connected people
# So to make it more better looking the current line is cleared (Whcih is input promt ), so the text of that is cleared and
# the message is printed,  so to make the continous flow , we use to print the cleared text during the printing of the message
# that is only one thing nothing else
