import customtkinter as ctk
from PIL import Image

class SceneTreeFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, title, values):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.checkboxes = []

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value)
            checkbox.grid(row=i, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes

class BottomTabs(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        #add the necessary tabs
        self.add("Render Details")
        self.add("Console")

        ### Render Details ###
        self.label = ctk.CTkLabel(master=self.tab("Render Details"), text= "Imagine render details here")
        self.label.grid(row=0, column=0, padx=20, pady=10)

        ### Console ###
        self.label = ctk.CTkLabel(master=self.tab("Console"), text="Imagine console-y stuff here")
        self.label.grid(row=0, column=0, padx=20, pady=10)

class FileBox(ctk.CTkScrollableFrame):
    def __init__(self, master, title, values):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.checkboxes = []

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value)
            checkbox.grid(row=i, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes

class RenderPreview(ctk.CTkLabel):
    image = Image
    def __init__(self, master, img, **kwargs):
        self.image = img
        
        super().__init__(master, **kwargs, image=ctk.CTkImage(self.image, size=(640,480)), text="")
        # self.bind("<Configure>", self._resize_image)
    
    def _resize_image(self,event):
        new_width = self.winfo_width()
        new_height = self.winfo_height()
        self.configure(image=ctk.CTkImage(self.image, size=(new_width,new_height)))

    def _update(self, master, img, **kwargs):
        img.size = (self.winfo_width(), self.winfo_height())
        self.image = img
        super().__init__(master, **kwargs, image=self.image, text="")

class PropertyEditor(ctk.CTkScrollableFrame):
    def __init__(self, master, title, values):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.checkboxes = []

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value)
            checkbox.grid(row=i, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes

class Root(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Get Raytraced")
        self.geometry("1280x720")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        values = ["value 1", "value 2", "value 3", "value 4", "value 5", "value 6"]
        self.scenetree_frame = SceneTreeFrame(self, title="Scene Tree", values=values)
        self.scenetree_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.property_editor = PropertyEditor(self, title="Property Editor", values=values)
        self.property_editor.grid(row=0,column=2, rowspan=2, padx=10, pady=10, sticky="nwse")
       
        self.bottom_tabs = BottomTabs(master=self)
        self.bottom_tabs.grid(row=1, column=1, padx=1, pady=10, sticky="nwse")

        self.filebox = FileBox(self, title="FileSystem", values=values)
        self.filebox.grid(row=1, column=0, padx=1, pady=(10, 0), sticky="nsw")

        tmpimage = Image.open("C:\\Users\\TPSHu\\Downloads\\IMG_4142.png")
        self.render_preview = RenderPreview(self, tmpimage)
        self.render_preview.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
    
        

