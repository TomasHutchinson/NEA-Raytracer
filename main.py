import customtkinter as ctk
print("Hello World")

ctk.set_appearance_mode("dark")# Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

root = ctk.CTk()

def button_callback():
    print("button pressed")

button = ctk.CTkButton(root, text="my button", command=button_callback)
button.grid(row=0, column=0, padx=20, pady=20)

while 1:
    root.update()