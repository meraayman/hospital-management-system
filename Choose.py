"""MBA Hospital - entry point.

Run with:  python Choose.py

Flow: role selection -> login (checked only against the chosen role)
      -> doctor / receptionist dashboard -> logout returns here.
"""
from tkinter import Tk, Frame, Label, Button, BOTH
from tkinter import messagebox

import db
from config import PRIMARY, BUTTON
from ui_helpers import PlaceholderEntry, load_image, run_db, FAILED


def show_role_selection():
    """Show the first screen + login.

    Returns (role, user_id, name) after a successful login,
    or None if the user closed the window.
    """
    root = Tk()
    root.title("MBA Hospital")
    root.geometry("1920x1080")
    root.configure(bg=PRIMARY)

    result = {"user": None, "role": None}

    home_img = load_image(root, "Home page.png", (780, 580))
    logo_img = load_image(root, "Logo.png", (140, 115))
    back_img = load_image(root, "back_white.png", (40, 40))

    def add_images(frame):
        Label(frame, image=home_img, bd=0, bg=PRIMARY).place(x=700, y=100)
        Label(frame, image=logo_img, bd=0, bg=PRIMARY).place(x=30, y=0)

    # ------------------------------------------------------------------
    # Screen 1: choose role
    # ------------------------------------------------------------------
    main_frame = Frame(root, bg=PRIMARY)
    add_images(main_frame)

    Label(main_frame, text="Welcome! Please choose your role", font=("Roboto", 22, "bold"),
          bg=PRIMARY, fg="white").place(x=160, y=310)

    for i, role in enumerate(("Doctor", "Receptionist")):
        Button(main_frame, text=role, height=1, width=13, font=("Roboto", 28, "bold"),
               background=BUTTON, foreground="white", activebackground="#99cfdb",
               border=0, cursor="hand2",
               command=lambda r=role: open_login(r)).place(x=250, y=400 + i * 100)

    # ------------------------------------------------------------------
    # Screen 2: login
    # ------------------------------------------------------------------
    login_frame = Frame(root, bg=PRIMARY)
    add_images(login_frame)
    Button(login_frame, image=back_img, bg=PRIMARY, activebackground=PRIMARY, border=0,
           cursor="hand2", command=lambda: show_main()).place(x=1420, y=70)

    box = Frame(login_frame, bg=PRIMARY, width=350, height=350)
    box.place(x=100, y=300)

    title_lbl = Label(box, text="", font=("Roboto", 22, "bold"), bg=PRIMARY, fg="white")
    title_lbl.place(x=30, y=10)

    username = PlaceholderEntry(box, "Username", width=25, fg="white", border=0,
                                bg=PRIMARY, insertbackground="white", font=("Roboto", 14))
    username.place(x=30, y=80)
    Frame(box, width=280, height=2, bg="white").place(x=30, y=107)

    password = PlaceholderEntry(box, "Password", is_password=True, width=25, fg="white", border=0,
                                bg=PRIMARY, insertbackground="white", font=("Roboto", 14))
    password.place(x=30, y=150)
    Frame(box, width=280, height=2, bg="white").place(x=30, y=177)

    def do_login(_event=None):
        role = result["role"]
        user, pw = username.value(), password.value()
        if not user or not pw:
            messagebox.showerror("Error", "Fields cannot be empty")
            return

        found = run_db(db.authenticate, role, user, pw)
        if found is FAILED:
            return
        if not found:
            messagebox.showerror("Error", f"Invalid {role.lower()} username or password")
            return

        user_id, name = found
        result["user"] = (role, user_id, name)
        root.destroy()

    Button(box, width=12, pady=7, command=do_login, font=("Roboto", 14, "bold"), text="Login",
           bg=BUTTON, fg="white", border=0, cursor="hand2").place(x=200, y=215)
    username.bind("<Return>", do_login)
    password.bind("<Return>", do_login)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def show_main():
        login_frame.pack_forget()
        main_frame.pack(fill=BOTH, expand=True)

    def open_login(role):
        result["role"] = role
        title_lbl.config(text=f"{role} Login")
        username.reset()
        password.reset()
        main_frame.pack_forget()
        login_frame.pack(fill=BOTH, expand=True)

    show_main()
    root.mainloop()
    return result["user"]


def main():
    # Keep going until someone closes a window instead of logging out
    while True:
        user = show_role_selection()
        if user is None:
            break

        role, user_id, name = user
        if role == "Doctor":
            import screen_doctor1
            action = screen_doctor1.run(user_id, name)
        else:
            import screen_receptionist
            action = screen_receptionist.run(user_id, name)

        if action != "logout":
            break


if __name__ == "__main__":
    main()
