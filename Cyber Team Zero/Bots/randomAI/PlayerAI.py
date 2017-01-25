from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import random

class PlayerAI:
    def __init__(self):
        pass

    def do_move(self, world, enemy_units, friendly_units):
        print()
        for i in range(len(friendly_units)):
            self.move_friendly(world, friendly_units[i], enemy_units)
        print()

    def move_friendly(self, world, friendly_unit, enemy_units):
        if (friendly_unit.health <= 0):
            print(str(friendly_unit.call_sign) + ": I'm dead")
            return

        # Find someone to shoot at
        for enemy in enemy_units:
            # Can we hit the enemy?
            if friendly_unit.check_shot_against_enemy(enemy) == ShotResult.CAN_HIT_ENEMY:
                print(str(friendly_unit.call_sign) + ": Shooting at " + str(enemy.call_sign))
                friendly_unit.shoot_at(enemy)
                break
            else:
                friendly_unit.move(random.choice(list(Direction)))



