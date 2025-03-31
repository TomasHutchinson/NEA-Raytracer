import customtkinter as ctk

#custom files
import user_interface

print("Hello World")

ctk.set_appearance_mode("dark")# Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green


root = user_interface.Root()

root.mainloop()
