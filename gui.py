import tkinter as tk
import requests
import threading
import time

HOST = "http://localhost:10000/state"
WIDTH = 1500
HEIGHT = 900


class BlobGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador de generación")

        tk.Label(self.root, text="Velocidad de actualización").pack()
        self.speed_var = tk.DoubleVar(value=1.0)
        tk.Scale(self.root,
                 from_=0.1, to=5.0,
                 resolution=0.1,
                 orient="horizontal",
                 variable=self.speed_var).pack(fill="x")

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()

        self.blob_drawables = {}
        self.food_drawables = {}

        self.running = True

        threading.Thread(target=self.update_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    def close(self):
        self.running = False
        self.root.destroy()

    def update_loop(self):
        while self.running:
            try:
                res = requests.get(HOST, timeout=1)
                if res.status_code == 200:
                    data = res.json()
                    self.update_canvas(data["blobs"], data["foods"])
            except Exception as e:
                print("GUI ERROR:", e)

            time.sleep(1 / self.speed_var.get())

    def update_canvas(self, blobs, foods):
        current_blobs = set()

        for b in blobs:
            if not b["alive"]:
                continue

            jid = b["jid"]
            x, y = b["x"], b["y"]

            returning = b["returning"]
            arrived_home = b.get("arrived_home", False)

            mutation = b.get("mutation", "none")

            if arrived_home:
                color = "#ffffff"  
            elif returning:
                color = "#ffffff" 
            else:
                if mutation == "none":
                    color = "#00aaff"  
                elif mutation == "speed":
                    color = "#ff0000" 
                elif mutation == "energy":
                    color = "#ffa500"  
                else:
                    color = "#00aaff"

            r = 6

            if jid in self.blob_drawables:
                for item in self.blob_drawables[jid]:
                    self.canvas.delete(item)

            items = []


            if arrived_home:
                halo = self.canvas.create_oval(
                    x - 12, y - 12,
                    x + 12, y + 12,
                    outline="#ffffff",
                    width=3
                )
                items.append(halo)


            elif returning:
                halo = self.canvas.create_oval(
                    x - 10, y - 10,
                    x + 10, y + 10,
                    outline="#ffffff",
                    width=2
                )
                items.append(halo)


            dot = self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=color,
                outline=color
            )
            items.append(dot)

            self.blob_drawables[jid] = items
            current_blobs.add(jid)

        for jid in list(self.blob_drawables.keys()):
            if jid not in current_blobs:
                for item in self.blob_drawables[jid]:
                    self.canvas.delete(item)
                del self.blob_drawables[jid]

        current_foods = set()

        for i, f in enumerate(foods):
            fx, fy = f["x"], f["y"]
            r = 4
            fid = f"food_{i}"

            if fid in self.food_drawables:
                self.canvas.coords(self.food_drawables[fid], fx-r, fy-r, fx+r, fy+r)
            else:
                self.food_drawables[fid] = self.canvas.create_oval(
                    fx - r, fy - r,
                    fx + r, fy + r,
                    fill="yellow",
                    outline="yellow"
                )

            current_foods.add(fid)

        for fid in list(self.food_drawables.keys()):
            if fid not in current_foods:
                self.canvas.delete(self.food_drawables[fid])
                del self.food_drawables[fid]


if __name__ == "__main__":
    BlobGUI()
