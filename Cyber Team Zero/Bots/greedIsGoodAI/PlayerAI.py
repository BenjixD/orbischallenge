from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from PythonClientAPI.libs.Game.Weapon import *
from random import randint

import operator

#last guy to get gun (meetup spot)
TEAM_MEETUP = [0,1,2,3]

class teamUp:
    def __init__(self):
        self.moves = None
        self.playerIndex = None

    def __init__(self, moves, index):
        self.moves = moves
        self.playerIndex = index

    def getMoves(teamUp):
        return teamUp.moves

class bestMoves:
    def __init__(self, unit):
        self.unit = unit
        self.closestWep = None
        self.closestWepObj = None
        self.closestWepLoc = None
        self.playerLink = []
        self.combatEnemy = []
        self.unhittableEnemy = []
        self.isBlocked = False

class PlayerAI:
    def __init__(self):
        pass    

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.
        
        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """

        #SET position of best guns
        rifle = world.get_positions_of_pickup_type(PickupType.WEAPON_LASER_RIFLE);
        sniper = world.get_positions_of_pickup_type(PickupType.WEAPON_RAIL_GUN);
        shotgun = world.get_positions_of_pickup_type(PickupType.WEAPON_SCATTER_GUN);

        #SET list of control points
        controlPoints = world.control_points;
        notMyControls = findControlList(controlPoints, friendly_units[0].team); 

        #STUFF ABOUT PLAYERS!!!!!
        #print (friendly_units[0].current_weapon_type);
        #print (friendly_units[0].health);

        #Init best moves unit
        f_best = [bestMoves(friendly_units[0]), bestMoves(friendly_units[1]), bestMoves(friendly_units[2]), bestMoves(friendly_units[3])];

        #Find closest Allies
        f_best = sortAllies(f_best, world);

        #Update the meetup
        updateMeetup(f_best);

        #Find Best Gun (Setup Rifle Priority System)
        f_best = findClosestWep(f_best, PickupType.WEAPON_SCATTER_GUN, shotgun, world);
        f_best = findClosestWep(f_best, PickupType.WEAPON_LASER_RIFLE, rifle, world);
        f_best = findClosestWep(f_best, PickupType.WEAPON_RAIL_GUN, sniper, world);


        #Move to Gun, Otherwise Support Teammate (if you have gun)
        #Move units to capture if Guns have been obtained
        #Assist Allies in Capture Point
        for i in f_best:
            if i.unit.current_weapon_type == WeaponType.MINI_BLASTER:
                if not(rifle) and not(sniper) and not(shotgun):
                    if notMyControls:
                        i.unit.move_to_destination(findClosestControl(notMyControls, f_best[TEAM_MEETUP[0]].unit.position, world));

                    else:
                        i.unit.move_to_destination(enemy_units[0].position);

                else:
                    print(i.unit.move_to_destination(i.closestWepLoc));
            else:
                for j in i.playerLink:
                    if f_best[j.playerIndex].unit.current_weapon_type == WeaponType.MINI_BLASTER and f_best[j.playerIndex].unit.health > 0:
                        print(i.unit.move_to_destination(f_best[j.playerIndex].unit.position))
                        break

                    elif i.playerLink[-1] == j:
                        if notMyControls:
                            i.unit.move_to_destination(findClosestControl(notMyControls, f_best[TEAM_MEETUP[0]].unit.position, world));

                        else:
                            i.unit.move_to_destination(enemy_units[0].position);


        #If you are on the best gun, pick it up
        for i in f_best:
            if i.unit.check_pickup_result() and i.unit.position == i.closestWepLoc:
                i.unit.pickup_item_at_position()

        #Check if previous turn blocked
        #Unblock Deadlock using random set scenario
        for i in f_best:
            if i.unit.last_move_result != MoveResult.MOVE_COMPLETED:
                print("HELP I AM BLOCKED")
                i.isBlocked = True

        #Check if all is blocked
        allIsBlocked = True
        for i in f_best:
            allIsBlocked = i.isBlocked and allIsBlocked

        print(allIsBlocked)

        #How to fix all is blocked (use rand)
        if allIsBlocked:
            while True:
                unBlockPoints = []
                for i in f_best:
                    direction = None;
                    random_direction_index = randint(0,7);
                    if(random_direction_index == 0):
                        direction = Direction.EAST
                    elif(random_direction_index == 1):
                        direction = Direction.NORTH
                    elif(random_direction_index == 2):
                        direction = Direction.NORTH_EAST
                    elif(random_direction_index == 3):
                        direction = Direction.NORTH_WEST
                    elif(random_direction_index == 4):
                        direction = Direction.SOUTH
                    elif(random_direction_index == 5):
                        direction = Direction.SOUTH_EAST
                    elif(random_direction_index == 6):
                        direction = Direction.SOUTH_WEST
                    else:
                        direction = Direction.WEST

                    unBlockPoints.append((i.unit.position[0] + direction.value[0], i.unit.position[1] + direction.value[1]))
                    i.unit.move(direction)
                
                unBlockPoints = set(unBlockPoints)
                if len(unBlockPoints) == 4:
                    break


        #Fight others who are out of range
        #Move towards enemy units and draw aggro
        for i in f_best:
            for j in enemy_units:
                if ProjectileWeapon.check_shot_against_point(j, i.unit.position, world, j.current_weapon_type) == ShotResult.CAN_HIT_ENEMY and j.health > 0:
                    i.unit.move_to_destination(j.position);
                    i.unhittableEnemy.append(j)

        #Shoot at anyone you see
        for i in f_best:
            for j in enemy_units:
                if i.unit.check_shot_against_enemy(j) == ShotResult.CAN_HIT_ENEMY and j.health > 0:
                    i.unit.shoot_at(j)
                    i.combatEnemy.append(j)


        #pre-compute the list of enemies within combat range
        #Use a set intersection algorithm to determine focus fire  
        flatten = [];
        for j in f_best:
            for k in j.combatEnemy:
                flatten.append(k)

        flatten.sort(key=operator.attrgetter('position'));

        #Check other units in range (focus-fire) using set intersection
        for i in f_best:
            maxOccur = 0
            currOccur = 0
            focusFire = [];
            previousEnemy = None;
            for j in flatten:
                if (previousEnemy == j or previousEnemy == None) and j in i.combatEnemy:
                    currOccur += 1
                    if currOccur > maxOccur:
                        maxOccur = currOccur
                        focusFire = [[j] * maxOccur]
                    elif currOccur == maxOccur:
                        focusFire.append([j] * maxOccur)
                else:
                    currOccur = 0
                    previousEnemy = None
            i.combatEnemy = focusFire
            if i.combatEnemy:
                i.unit.shoot_at(i.combatEnemy[0][0])

        #Micro Move units to enemy
        for i in f_best:
            for j in i.playerLink:
                if f_best[j.playerIndex].combatEnemy and not(i.combatEnemy) and not(i.unhittableEnemy):    #if closest unit has/is in combat
                    facingDirection = world.get_next_direction_in_path(f_best[j.playerIndex].unit.position, f_best[j.playerIndex].combatEnemy[0][0].position)
                    resultingPos = (f_best[j.playerIndex].unit.position[0] + facingDirection.value[0], f_best[j.playerIndex].unit.position[1] + facingDirection.value[1])
                    if i.unit.check_move_to_destination(resultingPos) != MoveResult.MOVE_VALID:                       #Case where our fighting player is blocking support
                        if facingDirection == Direction.NORTH or facingDirection == Direction.SOUTH:
                            nextPosLeft = (i.unit.position[0] + facingDirection.value[0], i.unit.position[0] - 1)
                            nextPosRight = (i.unit.position[0] + facingDirection.value[0], i.unit.position[0] + 1)
                            if i.unit.check_move_to_destination(nextPosLeft) == MoveResult.MOVE_VALID:  
                                i.unit.move_to_destination(nextPosLeft)
                            elif i.unit.check_move_to_destination(nextPosRight) == MoveResult.MOVE_VALID: 
                                i.unit.move_to_destination(nextPosRight)

                        elif facingDirection == Direction.EAST or facingDirection == Direction.WEST:
                            nextPosUp = (i.unit.position[0] - 1, i.unit.position[0] + facingDirection.value[1])
                            nextPosDown = (i.unit.position[0] + 1, i.unit.position[0] + facingDirection.value[1])
                            if i.unit.check_move_to_destination(nextPosUp) == MoveResult.MOVE_VALID:  
                                i.unit.move_to_destination(nextPosUp)
                            elif i.unit.check_move_to_destination(nextPosDown) == MoveResult.MOVE_VALID: 
                                i.unit.move_to_destination(nextPosDown)

                        elif facingDirection == Direction.NORTH_EAST or facingDirection == Direction.NORTH_WEST or facingDirection == Direction.SOUTH_EAST or facingDirection == Direction.SOUTH_WEST:
                            nextPosVertical = (i.unit.position[0], 0)
                            nextPosHorizontal = (0, i.unit.position[0])
                            if i.unit.check_move_to_destination(nextPosVertical) == MoveResult.MOVE_VALID:  
                                i.unit.move_to_destination(nextPosVertical)
                            elif i.unit.check_move_to_destination(nextPosHorizontal) == MoveResult.MOVE_VALID: 
                                i.unit.move_to_destination(nextPosHorizontal)

                    else:
                        i.unit.move_to_destination(resultingPos)

        #Priority Health Packet
        for i in f_best:
            if world.get_pickup_at_position(i.unit.position) and world.get_pickup_at_position(i.unit.position).pickup_type == PickupType.REPAIR_KIT:
                i.unit.pickup_item_at_position()

            



#Finds the closest weapon to person
def findClosestWep(f_best, wep_def, wep_pos, world):
    for unit in f_best:
        for wep in wep_pos:
            if unit.closestWep == None or world.get_path_length(unit.unit.position, wep) < unit.closestWep:    
                unit.closestWep = world.get_path_length(unit.unit.position,wep)
                unit.closestWepLoc = wep
                unit.closestWepObj = wep_def
            

    return f_best

#finds the closest allies to move to
def sortAllies(f_best, world):
    for i in range(0,len(f_best),1):
        lower = i + 1
        upper = i + len(f_best)
        for j in range(lower, upper,1):
            f_best[i].playerLink.append(teamUp(world.get_path_length(f_best[i].unit.position, f_best[j%4].unit.position), j%4))
        f_best[i].playerLink.sort(key=operator.attrgetter('moves'))
    
    return f_best;

#To update the meetup location
def updateMeetup(f_best):
    global TEAM_MEETUP;
    newMeetup = [];
    if not(len(TEAM_MEETUP) == 1):
        for i in range(0,len(f_best)):
            if f_best[i].unit.current_weapon_type == WeaponType.MINI_BLASTER:
                newMeetup.append(i)
        if newMeetup:
            TEAM_MEETUP=newMeetup

def findControlList(controlList, team):
    notMyControls = [];
    for i in controlList:
        if not(i.controlling_team == team):
            notMyControls.append(i);

    return notMyControls

def findClosestControl(controlList, unitPos, world):
    minDist = None;
    control = None;
    for i in controlList:
        if(minDist == None or world.get_path_length(unitPos, i.position) < minDist):
            minDist = world.get_path_length(unitPos, i.position)
            control = i

    return control.position