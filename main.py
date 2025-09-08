import customtkinter as ctk

#custom files
import user_interface

if __name__ == "__main__":
    print("Hello World")

    ctk.set_appearance_mode("dark")#Modes: system (default), light, dark
    ctk.set_default_color_theme("dark-blue")  #Themes: blue (default), dark-blue, green


    root = user_interface.Root()
    root.mainloop() #start the window loop 
