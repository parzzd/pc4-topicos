import random
import ast
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from blob import BlobAgent

WIDTH = 1500
HEIGHT = 900


def spawn_food_center():
    return (
        random.randint(int(WIDTH * 0.15), int(WIDTH * 0.85)),
        random.randint(int(HEIGHT * 0.15), int(HEIGHT * 0.85))
    )


class EnvironmentAgent(Agent):

    async def setup(self):
        print("[ENV] EnvironmentAgent iniciado.")

        self.state = {}   
        self.foods = []   
        self.day = 0

        self.blobs_alive = []
        self.pending_children = []

        self.add_behaviour(self.StateReceiver())
        self.add_behaviour(self.DayCycle(period=0.2))

    class StateReceiver(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=0.1)
            if not msg:
                return

            msg_type = msg.get_metadata("type")


            if msg_type == "state":
                body = ast.literal_eval(msg.body)
                jid = body["jid"]
                self.agent.state[jid] = body
                return

            if msg_type == "request_child":
                data = ast.literal_eval(msg.body)
                self.agent.pending_children.append(data)


    class DayCycle(PeriodicBehaviour):
        async def on_start(self):
            self.agent.start_new_day()

        async def run(self):
            self.agent.update_food()

            await self.agent.spawn_children()

            await self.agent.check_population()


    def start_new_day(self):
        print(f"\n===== NUEVO DÍA {self.day} =====")

        self.foods = [spawn_food_center() for _ in range(40)]
        self.pending_children = []

        for jid, b in self.state.items():
            b["food_eaten"] = 0
            b["returning"] = False
            b["arrived_home"] = False
            b["alive"] = True

    def update_food(self):
        pass

    async def spawn_children(self):
        if not self.pending_children:
            return

        for info in self.pending_children:
            parent_jid = info["jid"]
            upgrade = info["upgrade"]
            speed = info["speed"]
            energy = info["energy"]

            username = parent_jid.split("@")[0]
            new_jid = f"{username}_child_{random.randint(1000,9999)}@localhost"

            new_blob = BlobAgent(new_jid, "1234")
            new_blob.environment_jid = str(self.jid)

            new_blob.speed = speed
            new_blob.energy = energy
            new_blob.upgrade = upgrade

            await new_blob.start()
            self.state[new_jid] = {
                "jid": new_jid,
                "x": 0, "y": 0,
                "alive": True,
                "upgrade": upgrade
            }

            print(f"nuevo hijo creado: {new_jid}")

        self.pending_children = []

    async def check_population(self):
        alive = [b for b in self.state.values() if b["alive"]]

        if len(alive) == 0:
            print("HAN MUERTO. REINICIANDO")

            self.state = {}

            for i in range(25):
                jid = f"blob_{i}@localhost"
                blob = BlobAgent(jid, "1234")
                blob.environment_jid = str(self.jid)
                await blob.start()

                self.state[jid] = {
                    "jid": jid,
                    "alive": True
                }

            self.day = 0

        else:
            self.day += 1
            if self.day % 12 == 0:
                self.start_new_day()
