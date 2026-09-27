import os

# Resolve image paths relative to this file so the app runs on any machine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "Images")

from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk

login= Tk()
login.title("MBA Hospital - Login")
login.geometry("1920x1080")
login.configure(bg="#32acc7")
## Adding Image
home = Image.open(os.path.join(IMG_DIR, "Home page.png")).resize((780,580))
home = ImageTk.PhotoImage(home)
home_label=Label(login, image=home, bd=0, bg="#32acc7")
home_label.place(x=700,y=150)

logo = Image.open(os.path.join(IMG_DIR, "Logo.png")).resize((140,115))
logo = ImageTk.PhotoImage(logo)
logo_label=Label(login, image=logo, bd=0, bg="#32acc7")
logo_label.place(x=50,y=50)

## Input data
def logIn():
    un=userName.get()
    pw=password.get()

    if un=="Batool" and pw=="1234":
        messagebox.showinfo("Correct", "Login Succefully!")
    elif un!="Batool" and pw!="1234":
        messagebox.showerror("Invalid", "Invalid username and password")
    elif un!="Batool":
        messagebox.showerror("Invalid", "Invalid username")
    elif pw!="1234":
        messagebox.showerror("Invalid", "Invalid password")

## Create Frame
login_frame=Frame(login, bg="#32acc7", width=350,height=350)
login_frame.place(x=100,y=300)

## Username entry
def on_enter(e):
    userName.delete(0, "end")
def on_leave(e):
    name=userName.get()
    if name=="":
        userName.insert(0,"Username")

userName= Entry(login_frame, width=25, fg="white", border=0, bg="#32acc7", font=("Roboto", 14))
userName.place(x=30, y=80)
userName.insert(0, "Username")
userName.bind("<FocusIn>", on_enter)
userName.bind("<FocusOut>", on_leave)

Frame(login_frame, width=280, height=2, bg="white").place(x=30, y=107)

## Password entry
def on_enter(e):
    password.delete(0, "end")
def on_leave(e):
    name=password.get()
    if name=="":
        password.insert(0,"Password")
password= Entry(login_frame, width=25, fg="white", border=0, bg="#32acc7", font=("Roboto", 14))
password.place(x=30, y=150)
password.insert(0, "Password")
password.bind("<FocusIn>", on_enter)
password.bind("<FocusOut>", on_leave)

Frame(login_frame, width=280, height=2, bg="white").place(x=30, y=177)

## Login Button
Button(login_frame, width=12, pady=7, command=logIn, font=("Roboto",14,"bold"), text="Login",bg="#0088a6", fg="white", border=0).place(x=200, y=215)

## logout button
logout = Image.open(os.path.join(IMG_DIR, "Log out button.png")).resize((30,30))
logout = ImageTk.PhotoImage(logout)
logout_label=Label(login, image=logout, bd=0, bg="#32acc7")
logout_label.place(x=1420,y=70)

logout_btn= Button(login, image=logout, bg="#32acc7", bd=0)
logout_btn.place(x=1420, y=70)

login.mainloop()