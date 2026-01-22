import customtkinter as ctk
from tkinter import filedialog
import os
from PIL import Image
import numpy as np

#custom stuff
import renderer
import console
import scene
import objects

class SceneTreeFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, title, on_select=None):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.on_select = on_select
        self.checkboxes = []
        self.obj_map = {}  # name -> actual object
        self.update_scene_tree()

    def update_scene_tree(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        self.obj_map.clear()

        def make_unique_names(items):
            seen = {}
            unique_names = []
            for item in items:
                base_name = str(item.name)
                if base_name not in seen:
                    seen[base_name] = 0
                    unique_names.append(base_name)
                else:
                    seen[base_name] += 1
                    unique_name = f"{base_name}{seen[base_name]}"
                    unique_names.append(unique_name)
            return unique_names

        row = 0
        obj_label = ctk.CTkLabel(self, text="Objects", font=("", 14, "bold"))
        obj_label.grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1

        if hasattr(scene, "scene") and hasattr(scene.scene, "objects"):
            object_names = make_unique_names(scene.scene.objects)
            for i, (obj, display_name) in enumerate(zip(scene.scene.objects, object_names)):
                btn = ctk.CTkButton(self, text=display_name, command=lambda o=obj: self.on_object_selected(o))
                btn.grid(row=row, column=0, padx=20, pady=(2, 0), sticky="w")
                self.obj_map[display_name] = obj
                row += 1

        light_label = ctk.CTkLabel(self, text="Lights", font=("", 14, "bold"))
        light_label.grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1

        if hasattr(scene, "scene") and hasattr(scene.scene, "lights"):
            light_names = make_unique_names(scene.scene.lights)
            for j, (light, display_name) in enumerate(zip(scene.scene.lights, light_names)):
                btn = ctk.CTkButton(self, text=display_name, command=lambda l=light: self.on_object_selected(l))
                btn.grid(row=row, column=0, padx=20, pady=(2, 0), sticky="w")
                self.obj_map[display_name] = light
                row += 1
        
        camera_label = ctk.CTkLabel(self, text="Camera", font=("", 14, "bold"))
        camera_label.grid(row=row, column=0, padx=10, pady=(10, 5), sticky="w")
        row += 1
        btn = ctk.CTkButton(self, text="Camera", command=lambda l=scene.scene.camera: self.on_object_selected(l))
        btn.grid(row=row, column=0, padx=20, pady=(2, 0), sticky="w")
        self.obj_map["Camera"] = scene.scene.camera
        row += 1

    def on_object_selected(self, obj):
        print(f"Selected: {obj.name}")
        if callable(self.on_select):
            self.on_select(obj)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes

class BottomTabs(ctk.CTkTabview):
    console_lines = console.console.buffer

    def __init__(self, master, render_frame, **kwargs):
        super().__init__(master, **kwargs)
        self.render_frame = render_frame

        # Default render settings
        self.render_settings = {
            "render_scale": 0.25,
            "num_x_chunks": 4,
            "num_y_chunks": 4,
            "samples": 2
        }

        # Add tabs
        self.add("Render Details")
        self.add("Console")

        # ---------------- Render Details ----------------
        tab_render = self.tab("Render Details")
        row = 0

        # Render settings inputs
        self.entries = {}
        for key, value in self.render_settings.items():
            label = ctk.CTkLabel(tab_render, text=key.replace("_", " ").capitalize())
            label.grid(row=row, column=0, padx=20, pady=(5, 0), sticky="w")

            entry = ctk.CTkEntry(tab_render, width=100)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=20, pady=(5, 0), sticky="w")
            self.entries[key] = entry
            row += 1

        # Render button
        self.render_button = ctk.CTkButton(tab_render, text="Render Image", command=self.on_render_pressed)
        self.render_button.grid(row=row, column=0, columnspan=2, padx=20, pady=10)

        # ---------------- Console ----------------
        tab_console = self.tab("Console")
        self.console_bg = ctk.CTkScrollableFrame(tab_console, height=200)
        self.console_bg.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        tab_console.grid_columnconfigure(0, weight=1)
        self.console_bg.grid_columnconfigure(0, weight=1)
        tab_console.grid_rowconfigure(0, weight=0)

        self.console_text = ctk.CTkLabel(self.console_bg, text="", justify="left")
        self.console_text.grid(row=0, column=0, sticky="w")
        self.update_console()

    def on_render_pressed(self):
        # Read values from entries and update settings
        for key, entry in self.entries.items():
            try:
                self.render_settings[key] = float(entry.get()) if "scale" in key else int(entry.get())
            except ValueError:
                print(f"Invalid value for {key}, using default {self.render_settings[key]}")

        # Pass updated settings to the render frame
        self.render_frame._render(
            render_scale=self.render_settings["render_scale"],
            num_x_chunks=self.render_settings["num_x_chunks"],
            num_y_chunks=self.render_settings["num_y_chunks"],
            samples=self.render_settings.get("samples", 64)
        )

    def update_console(self):
        self.console_lines = console.console.buffer
        nt = ""
        for l in self.console_lines:
            nt += l + "\n"
        self.console_text.configure(text=nt)
    

class FileBox(ctk.CTkScrollableFrame):
    def __init__(self, master, title, scene_tree):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        self.scene_tree = scene_tree  # <-- keep reference to the SceneTreeFrame

        # Buttons for filesystem operations
        browse_obj_btn = ctk.CTkButton(self, text="Add .OBJ to Scene", command=self.open_obj_file)
        browse_obj_btn.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="we")

        browse_scn_btn = ctk.CTkButton(self, text="Load .SCN Scene", command=self.open_scn_file)
        browse_scn_btn.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="we")

        save_scn_btn = ctk.CTkButton(self, text="Save Current Scene", command=self.save_scene)
        save_scn_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="we")

        # A label for showing file operations
        self.status_label = ctk.CTkLabel(self, text="No file selected", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="w")

    # ----------- FILE DIALOGS ---------------

    def open_obj_file(self):
        """Open file dialog for selecting a .obj file."""
        filepath = filedialog.askopenfilename(
            title="Select OBJ File",
            filetypes=[("OBJ Files", "*.obj"), ("All Files", "*.*")]
        )
        if filepath:
            self.status_label.configure(text=f"Loaded OBJ: {os.path.basename(filepath)}")
            print(f"[FileBox] Adding OBJ: {filepath}")

            try:
                # Add to scene
                name = os.path.basename(filepath).rsplit(".", 1)[0]
                scene.scene.objects.append(objects.mesh(filepath=filepath, name=name))
                # Update the scene tree
                self.scene_tree.update_scene_tree()
                print(f"[FileBox] SceneTree updated after adding {name}")
            except Exception as e:
                print(f"Error loading OBJ: {e}")

    def open_scn_file(self):
        """Open file dialog for selecting a .scn scene file."""
        filepath = filedialog.askopenfilename(
            title="Select Scene File",
            filetypes=[("Scene Files", "*.scn"), ("All Files", "*.*")]
        )
        if filepath:
            self.status_label.configure(text=f"Scene loaded: {os.path.basename(filepath)}")
            print(f"[FileBox] Loading scene: {filepath}")

            try:
                scene.load_scene(filepath)
                self.scene_tree.update_scene_tree()
            except Exception as e:
                print(f"Error loading scene: {e}")

    def save_scene(self):
        """Open file dialog for saving current scene."""
        filepath = filedialog.asksaveasfilename(
            title="Save Scene As",
            defaultextension=".scn",
            filetypes=[("Scene Files", "*.scn"), ("All Files", "*.*")]
        )
        if filepath:
            self.status_label.configure(text=f"Scene saved: {os.path.basename(filepath)}")
            print(f"[FileBox] Saving scene: {filepath}")

            try:
                scene.save_scene(filepath)
                self.scene_tree.update_scene_tree()
            except Exception as e:
                print(f"Error saving scene: {e}")

class RenderPreview(ctk.CTkLabel):
    image = Image
    def __init__(self, master, img, **kwargs):
        self.image = img
        
        super().__init__(master, **kwargs, image=ctk.CTkImage(self.image, size=(640,480)), text="", corner_radius=5)
        self.bind("<Configure>", self._resize_image)
    
    def _resize_image(self,event):
        new_width = self.winfo_width()
        new_height = self.winfo_height()
        self.configure(image=ctk.CTkImage(self.image, size=(new_width,new_height)))
    
    def _render(self, render_scale = 0.25, num_x_chunks=4,num_y_chunks=4,samples=2):
        new_width = self.winfo_width()
        new_height = self.winfo_height()
        target_size = (int(new_width * render_scale), int(new_height * render_scale))

        def update_frame(generator):
            try:
                frame = next(generator)
                self.image = frame
                self.configure(image=ctk.CTkImage(self.image, size=(new_width, new_height)))
                # Schedule next update (don’t block UI)
                self.after(50, lambda: update_frame(generator))
            except StopIteration:
                print("Rendering complete")

        gen = renderer.render_stream(target_size, num_x_chunks=num_x_chunks, num_y_chunks=num_y_chunks, samples=samples)
        update_frame(gen)

    def _update(self, master, img, **kwargs):
        img.size = (self.winfo_width(), self.winfo_height())
        self.image = img
        super().__init__(master, **kwargs, image=self.image, text="")



class PropertyEditor(ctk.CTkScrollableFrame):
    def __init__(self, master, title, editable_keys=None):
        super().__init__(master, label_text=title)
        self.grid_columnconfigure(0, weight=1)
        # Keys we want to allow editing
        self.editable_keys = editable_keys or ["name", "transform", "intensity", "direction", "position", "fov"]
        self.entries = {}  # key -> entry or list of entries
        self.current_obj = None

    def show_properties(self, obj):
        """Display the properties of the selected object."""
        # Clear previous
        for widget in self.winfo_children():
            widget.destroy()
        self.entries.clear()
        self.current_obj = obj

        row = 0
        title = ctk.CTkLabel(self, text=f"Editing: {obj.name}", font=("", 14, "bold"))
        title.grid(row=row, column=0, padx=10, pady=(5, 10), sticky="w")
        row += 1

        for key in self.editable_keys:
            if hasattr(obj, key):
                value = getattr(obj, key)

                if key == "transform":
                    row = self._create_transform_section(row, value)
                else:
                    row = self._create_property_field(row, key, value)

    def _create_property_field(self, row, key, value):
        """Create entry widgets for scalars or arrays."""
        label = ctk.CTkLabel(self, text=key)
        label.grid(row=row, column=0, padx=10, pady=(5, 0), sticky="w")
        row += 1

        # Handle arrays or tuples
        if isinstance(value, (list, tuple, np.ndarray)):
            sub_entries = []
            frame = ctk.CTkFrame(self)
            frame.grid(row=row, column=0, padx=10, pady=(0, 5), sticky="we")
            for i, v in enumerate(value):
                entry = ctk.CTkEntry(frame, width=60)
                entry.insert(0, str(v))
                entry.grid(row=0, column=i, padx=3, pady=2)
                # Live update on enter or focus out
                entry.bind("<Return>", lambda e, k=key, es=sub_entries: self._apply_array_change(k, es))
                entry.bind("<FocusOut>", lambda e, k=key, es=sub_entries: self._apply_array_change(k, es))
                sub_entries.append(entry)
            self.entries[key] = sub_entries
        else:
            entry = ctk.CTkEntry(self)
            entry.insert(0, str(value))
            entry.grid(row=row, column=0, padx=10, pady=(0, 5), sticky="we")
            entry.bind("<Return>", lambda e, k=key: self._apply_single_change(k))
            entry.bind("<FocusOut>", lambda e, k=key: self._apply_single_change(k))
            self.entries[key] = entry
        row += 1
        return row

    def _create_transform_section(self, row, transform_obj):
        """Create live-editable rows for position, rotation, scale."""
        header = ctk.CTkLabel(self, text="Transform", font=("", 13, "bold"))
        header.grid(row=row, column=0, padx=10, pady=(5, 5), sticky="w")
        row += 1

        for attr in ["position", "rotation", "scale"]:
            value = getattr(transform_obj, attr)
            label = ctk.CTkLabel(self, text=attr.capitalize())
            label.grid(row=row, column=0, padx=10, pady=(2, 0), sticky="w")
            row += 1

            frame = ctk.CTkFrame(self)
            frame.grid(row=row, column=0, padx=10, pady=(0, 5), sticky="we")
            sub_entries = []

            for i, v in enumerate(value):
                entry = ctk.CTkEntry(frame, width=60)
                entry.insert(0, str(v))
                entry.grid(row=0, column=i, padx=3, pady=2)
                # Live update on enter or focus out
                entry.bind("<Return>", lambda e, a=attr, es=sub_entries: self._apply_transform_change(a, es))
                entry.bind("<FocusOut>", lambda e, a=attr, es=sub_entries: self._apply_transform_change(a, es))
                sub_entries.append(entry)

            self.entries[attr] = sub_entries
            row += 1

        return row

    # -------------------- APPLY CHANGES --------------------

    def _apply_single_change(self, key):
        if not self.current_obj:
            return
        entry = self.entries.get(key)
        if not entry:
            return
        text = entry.get()
        try:
            value = float(text)
        except ValueError:
            value = text
        setattr(self.current_obj, key, value)
        print(f"Updated {self.current_obj.name}.{key} = {value}")

    def _apply_array_change(self, key, entries):
        if not self.current_obj:
            return
        values = []
        for e in entries:
            try:
                values.append(float(e.get()))
            except ValueError:
                values.append(0.0)
        arr = np.array(values, dtype=float)
        setattr(self.current_obj, key, arr)
        print(f"Updated {self.current_obj.name}.{key} = {arr}")

    def _apply_transform_change(self, attr, entries):
        if not self.current_obj or not hasattr(self.current_obj, "transform"):
            return
        values = []
        for e in entries:
            try:
                values.append(float(e.get()))
            except ValueError:
                values.append(0.0)
        setattr(self.current_obj.transform, attr, np.array(values, dtype=float))
        print(f"Updated {self.current_obj.name}.transform.{attr} = {values}")

class Root(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Get Raytraced")
        self.geometry("1280x720")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

        tmpimage = Image.new('RGB', size=(1,1))
        self.render_preview = RenderPreview(self, tmpimage)
        self.render_preview.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")

        # property editor
        self.property_editor = PropertyEditor(self, title="Property Editor")
        self.property_editor.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nwse")

        # scene tree
        self.scenetree_frame = SceneTreeFrame(self, title="Scene Tree", on_select=self.property_editor.show_properties)
        self.scenetree_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")

        # bottom console
        self.bottom_tabs = BottomTabs(master=self, render_frame=self.render_preview)
        self.bottom_tabs.grid(row=1, column=1, padx=1, pady=10, sticky="nwse")

        # filesystem box
        self.filebox = FileBox(self, title="FileSystem", scene_tree=self.scenetree_frame)
        self.filebox.grid(row=1, column=0, padx=1, pady=(10, 0), sticky="nsw")