import random
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message


def spawn_on_edge(width, height):
    side = random.choice(["top", "bottom", "left", "right"])

    if side == "top":
        return random.randint(0, width), 0
    if side == "bottom":
        return random.randint(0, width), height
    if side == "left":
        return 0, random.randint(0, height)
    if side == "right":
        return width, random.randint(0, height)


class BlobAgent(Agent):

    class LifeCycleBehaviour(PeriodicBehaviour):
        async def on_start(self):
            self.blob = self.agent

        async def run(self):
            if not self.blob.alive:
                await self.report_state("dead")
                await self.kill()
                return

            if self.blob.food_eaten >= 1:
                self.move_towards(self.blob.home_x, self.blob.home_y)

                if self.distance(
                    self.blob.x, self.blob.y,
                    self.blob.home_x, self.blob.home_y
                ) < 15:
                    self.blob.arrived_home = True

                    msg = Message(to=self.agent.environment_jid)
                    msg.set_metadata("type", "request_child")
                    msg.body = str({
                        "jid": str(self.agent.jid),
                        "speed": self.blob.speed,
                        "energy": self.blob.energy,
                        "upgrade": self.blob.upgrade
                    })
                    await self.send(msg)

                await self.report_state("returning")
                return

            self.move_random()

            self.blob.energy -= 1
            if self.blob.energy <= 0:
                self.blob.alive = False


            if not self.blob.upgrade and random.random() < 0.01:
                self.blob.upgrade = True

                if random.random() < 0.5:
                    self.blob.speed += 0.5
                else:
                    self.blob.energy += 30

            await self.report_state("alive")

        def distance(self, x1, y1, x2, y2):
            return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

        def move_random(self):
            dx = random.uniform(-1, 1) * self.blob.speed
            dy = random.uniform(-1, 1) * self.blob.speed
            self.blob.x = max(0, min(self.blob.worldWidth, self.blob.x + dx))
            self.blob.y = max(0, min(self.blob.worldHeight, self.blob.y + dy))

        def move_towards(self, tx, ty):
            dx = tx - self.blob.x
            dy = ty - self.blob.y
            dist = max((dx*dx + dy*dy)**0.5, 0.01)
            self.blob.x += (dx/dist) * self.blob.speed
            self.blob.y += (dy/dist) * self.blob.speed

        async def report_state(self, status):
            msg = Message(to=self.agent.environment_jid)
            msg.set_metadata("type", "state")
            msg.body = str({
                "jid": str(self.agent.jid),
                "x": self.blob.x,
                "y": self.blob.y,
                "energy": self.blob.energy,
                "alive": self.blob.alive,
                "food_eaten": self.blob.food_eaten,
                "upgrade": self.blob.upgrade,
                "returning": self.blob.food_eaten >= 1,
                "arrived_home": self.blob.arrived_home,
                "status": status
            })
            await self.send(msg)

    async def setup(self):
        self.energy = getattr(self, "energy", 100)
        self.alive = True
        self.food_eaten = 0
        self.upgrade = getattr(self, "upgrade", False)
        self.arrived_home = False

        self.speed = getattr(self, "speed", random.uniform(1.0, 2.0))

        self.worldWidth = 1500
        self.worldHeight = 900

        if not hasattr(self, "x"):
            self.x, self.y = spawn_on_edge(self.worldWidth, self.worldHeight)

        self.home_x = self.x
        self.home_y = self.y

        self.environment_jid = None

        self.add_behaviour(self.LifeCycleBehaviour(period=0.2))
