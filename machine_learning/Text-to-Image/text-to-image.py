# text-to-image.py
# version 0.0.1
# Model: FLUX.1-dev
# GUI: Tkinter

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import torch
from diffusers import FluxPipeline
import threading

class FluxGUI:
    def __init__(self, master):
        self.master = master
        master.title("FLUX.1-dev Image Generator")
        master.geometry("1100x800")

        # Setup pipeline
        self.pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.float16)
        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()

        # GUI elements
        self.prompt_label = tk.Label(master, text="Enter prompt:")
        self.prompt_label.pack()

        self.prompt_entry = tk.Entry(master, width=50)
        self.prompt_entry.pack()

        self.generate_button = tk.Button(master, text="Generate Image", command=self.generate_image_thread)
        self.generate_button.pack()

        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.pack()

        self.image_label = tk.Label(master)
        self.image_label.pack()

    def generate_image_thread(self):
        self.generate_button.config(state=tk.DISABLED)
        threading.Thread(target=self.generate_image).start()

    def generate_image(self):
        prompt = self.prompt_entry.get()
        
        def callback(step, timestep, latents):
            progress = int((step / 50) * 100)
            self.progress['value'] = progress
            self.master.update_idletasks()

        image = self.pipe(
            prompt,
            height=768,
            width=768,
            guidance_scale=3.5,
            num_inference_steps=50,
            max_sequence_length=512,
            generator=torch.Generator("cuda").manual_seed(0),
            callback=callback,
            callback_steps=1
        ).images[0]

        self.display_image(image)
        self.generate_button.config(state=tk.NORMAL)

    def display_image(self, pil_image):
        tk_image = ImageTk.PhotoImage(pil_image)
        self.image_label.config(image=tk_image)
        self.image_label.image = tk_image

if __name__ == "__main__":
    root = tk.Tk()
    gui = FluxGUI(root)
    root.mainloop()
