import asyncio
import random
from aiohttp import web

WIDTH = 1500
HEIGHT = 900

state = {}
foods = []
DAY_DURATION = 12
POBLACION=100
COMIDAS=80

def spawn_on_edge():
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        return random.randint(0, WIDTH), 0
    if side == "bottom":
        return random.randint(0, WIDTH), HEIGHT
    if side == "left":
        return 0, random.randint(0, HEIGHT)
    if side == "right":
        return WIDTH, random.randint(0, HEIGHT)


def spawn_food_center():
    return (
        random.randint(int(WIDTH * 0.15), int(WIDTH * 0.85)),
        random.randint(int(HEIGHT * 0.15), int(HEIGHT * 0.85))
    )


class Blob:
    def __init__(self, blob_id, parent=None):
        self.id = blob_id


        if parent:
            self.x, self.y = spawn_on_edge()
            self.home_x, self.home_y = self.x, self.y

            self.speed = parent.speed
            self.energy = parent.energy
            self.upgrade = parent.upgrade
            self.mutation_type = parent.mutation_type

        else:
            self.x, self.y = spawn_on_edge()
            self.home_x, self.home_y = self.x, self.y

            self.speed = random.uniform(1.0, 2.0)
            self.energy = 100

            self.upgrade = False
            self.mutation_type = "none"

        self.alive = True
        self.arrived_home = False
        self.food_eaten = 0
        self.returning = False

    def distance_to(self, fx, fy):
        return ((self.x - fx)**2 + (self.y - fy)**2)**0.5

    def closest_food(self):
        if not foods:
            return None
        return min(foods, key=lambda f: self.distance_to(f[0], f[1]))

    def go_to_target(self, tx, ty):
        dx = tx - self.x
        dy = ty - self.y
        dist = max((dx*dx + dy*dy)**0.5, 0.001)
        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed

    def step(self):
        if not self.alive:
            return

        if self.returning:
            self.go_to_target(self.home_x, self.home_y)

            if self.distance_to(self.home_x, self.home_y) < 10:
                self.arrived_home = True
                self.energy = 100
            return


        target = self.closest_food()
        if target:
            fx, fy = target
            self.go_to_target(fx, fy)

            if self.distance_to(fx, fy) < 15:
                self.food_eaten += 1
                try:
                    foods.remove(target)
                except:
                    pass

                if self.food_eaten >= 1:
                    self.returning = True
                    return

        else:
            self.x += random.uniform(-1, 1) * self.speed
            self.y += random.uniform(-1, 1) * self.speed

        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))

        self.energy -= 1
        if self.energy <= 0:
            self.alive = False

        if not self.upgrade and random.random() < 0.01:
            self.upgrade = True

            if random.random() < 0.5:
                # mutación de velocidad
                self.speed += 0.5
                self.mutation_type = "speed"
            else:
                # mutación de energía
                self.energy += 30
                self.mutation_type = "energy"

    def to_dict(self):
        return {
            "jid": self.id,
            "x": self.x,
            "y": self.y,
            "energy": self.energy,
            "alive": self.alive,
            "upgrade": self.upgrade,
            "eaten": self.food_eaten,
            "returning": self.returning,
            "arrived_home": self.arrived_home,
            "mutation": self.mutation_type
        }



async def one_day(blobs):
    print("Nuevo día iniciado...")

    foods.clear()
    for _ in range(COMIDAS):
        foods.append(spawn_food_center())

    for b in blobs:
        b.energy = 100
        b.alive = True
        b.arrived_home = False
        b.food_eaten = 0
        b.returning = False

    for _ in range(int(DAY_DURATION / 0.05)):
        for b in blobs:
            b.step()
            state[b.id] = b
        await asyncio.sleep(0.05)

    survivors = [b for b in blobs if b.food_eaten >= 1]
    print("Sobrevivientes:", len(survivors))

    children = []
    for parent in survivors:
        child_id = f"{parent.id}_child_{random.randint(1000, 9999)}"
        child = Blob(child_id, parent=parent)
        children.append(child)

    print("Hijos generados:", len(children))


    no_mut = sum(1 for b in survivors if b.mutation_type == "none")
    speed_mut = sum(1 for b in survivors if b.mutation_type == "speed")
    energy_mut = sum(1 for b in survivors if b.mutation_type == "energy")

    print("======     ESTADÍSTICAS DEL DÍA     ======")
    print(f"Total sobrevivientes:   {len(survivors)}")
    print(f"Sin mutación:           {no_mut}")
    print(f"Mutación de velocidad:  {speed_mut}")
    print(f"Mutación de energía:    {energy_mut}")
    print(f"Hijos generados:        {len(children)}")
    print("==========================================\n")

    return survivors + children



async def simulation_loop(population):
    blobs = population

    while True:
        blobs = await one_day(blobs)

        if not blobs:
            print("Todos murieron. Reiniciando población.")
            blobs = [Blob(f"blob_{i}") for i in range(POBLACION)]


async def handle_state(request):
    return web.json_response({
        "blobs": [b.to_dict() for b in state.values()],
        "foods": [{"x": f[0], "y": f[1]} for f in foods]
    })


async def main():
    print("Iniciando blobs...")

    initial_blobs = [Blob(f"blob_{i}") for i in range(POBLACION)]

    global state
    state = {b.id: b for b in initial_blobs}

    app = web.Application()
    app.router.add_get("/state", handle_state)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "localhost", 10000)
    await site.start()

    print("Servidor en http://localhost:10000/state")

    await simulation_loop(initial_blobs)


if __name__ == "__main__":
    asyncio.run(main())
