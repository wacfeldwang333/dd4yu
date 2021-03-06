# ZebraCrossings, Lights, Sidewalks, Portals, MindControllers, stuff that matters but seems "virtual"
# Sidewalks are here because they work with ZCs

import concrete, carped
import random
from collections import OrderedDict
import math

class ZebraCrossing:
    # where pedestrians cross; pedestrians do not move continuously, but take x time to cross
    # since by law you aren't allowed to drive if the pedestrians are anywhere on the pavement
    # belongs to Road object

    def __init__(self, parent):  # parent is a Road1
        # when a pedestrian is crossing it adds 1 to numberofpedestrians, when it leaves it subtracts 1
        # the crossing checks when numberofpedestrians == 0 and then it becomes not occupied
        self.occupied = False
        self.peds = []
        self.parentroad = parent
        self.pedlight = Light(self)
        self.buttonpushed = False  # does what those buttons on telephone poles do IRL


    def setsidewalks(self):
        self.sw1 = self.parentroad.sw1
        self.sw2 = self.parentroad.sw2

    length = concrete.Lane.lanewidth * 6  # 3 Lanes in a Road, two Roads to cross (one from another intersection)

    def onetick(self):
        self.pedlight.state = self.parentroad.light.state

        # TODO: make MC deal with buttonpushed
        
        stayedinzc = []
        for p in self.peds:
            p.ticksfromspawn += 1
            p.walkingtimeleft -= 1
            if p.walkingtimeleft <= 0:
                p.currtarsw.peds.append(p)
                p.parent = p.currtarsw
                p.currtarsw = None
                p.currtarzc = None
                #p.beenherebefore = True
                p.justgothere = True
            else:
                stayedinzc.append(p)
        self.peds = list(stayedinzc)

    def getrelad(self, sw):  # oxymoron?
        # we get the absolute direction of this ZC, relative to one of its adjacent sidewalks
        road = self.parentroad
        if sw == road.sw1:  # then it's on the right side, relative to the road facing Middle
            return (road.absolutedir + 1) % 4
        else:  # sw == road.sw2
            return (road.absolutedir - 1) % 4
        print("Error in ZebraCrossing.getrelad()")

    def getoppositesw(self, sw):
        return self.sw1 if sw == self.sw2 else self.sw2


class Light:  # applies to traffic and pedestrian lights, since they are effectively the same, except in timing
    def __init__(self, parent):  # will figure out parenttype on its own
        self.state = 'r'  # same characters for pedestrian lights, in the matching which makes sense
        self.parenttype = 'z' if type(parent) is ZebraCrossing else 'r'
        self.parent = parent  # can be road or zebra crossing

        self.yellowtimeleft = None  # how long until it turns red (in ticks)
        self.timesince = 0

    mintime = 200
    yellowtime = 20  # FON, the amount of time a light will be yellow


class Sidewalk:
    # small square at the four corners of intersections, where pedestrians stay when not crossing roads
    def __init__(self, p, c1, c2):
        self.parent = p
        self.peds = []
        self.crossing1, self.crossing2 = c1, c2  # RTL, facing middle

        # roads are from right to left, Sidewalk's perspective facing the Middle
        self.road1 = self.crossing1.parentroad
        self.road2 = self.crossing2.parentroad

    def onetick(self):
        stayedinsw = []
        for p in self.peds:
            p.ticksfromspawn += 1
            if p.justgothere:
                p.justgothere = False
                currgc = self.parent.gridcoords
                nextgc = p.path[0].gridcoords  # check if it should should be 0 or 1
                ad = MindController.directiontotake(currgc, nextgc)  # check function name

                relad1 = self.crossing1.getrelad(self)  # check declaration
                relad2 = self.crossing2.getrelad(self)

                if ad == relad1:
                    p.currtarzc = self.crossing1
                elif ad == relad2:
                    p.currtarzc = self.crossing2
                else:  # taking a road next
                    p.currtarzc = self.parent.adjacents[ad]
                    if type(p.currtarzc) is concrete.Intersection:  # then we get the correct road
                        p.currtarzc = p.currtarzc.roads[(ad + 2) % 4]
                        
                    # if it's a Portal we don't do anything at the moment

                # push the button, and get currtarsw
                if type(p.currtarzc) is ZebraCrossing:
                    p.currtarzc.buttonpushed = True
                    p.currtarsw = p.currtarzc.getoppositesw(self)

            # now, if red light, do nothing, otherwise go on your way
            if type(p.currtarzc) is ZebraCrossing:
                if p.currtarzc.pedlight.state == 'g':
                    p.walkingtimeleft = p.timeleft(ZebraCrossing.length)
                    p.parent = p.currtarzc
                    p.currtarzc.peds.append(p)
                    p.currtarzc = None
                else:
                    stayedinsw.append(p)  # the only case you will stay
            elif type(p.currtarzc) is concrete.Road:
                p.currtarzc.offerroad(p)
            else:  # Portal
                p.currtarzc.offerportal(p)
                
        self.peds = list(stayedinsw)
                    
# I just realized how bad some editors can be - March 2 2018
class Portal:  # called Portal because cars/pedestrians start and end here (there are multiple portals)
    # attaches to road of intersection
    # cars coming from the intersection go directly from Middle to Portal

    def __init__(self, road, pos, p):
        self.cars = []
        self.peds = []
        self.adjroad = road  # the road it feeds into
        self.finished = []  # cars and peds who are done
        self.position = pos  # 0, 1, 2, 3 -> up, right, down, left, see MindController.decidedest()
        self.parent = p
        self.gridcoords = list(self.getgc())

    def createcar(self):
        newcar = carped.Car(self)
        self.cars.append(newcar)

        #return newcar  # gives car to MindController, the one that calls the function and decides the car's destination

    @staticmethod
    def elementwiseadd(v1, v2):  # 2D vector addition
        return [v1[0] + v2[0], v1[1] + v2[1]]
    
    adtoadding = {  # how the corods change relative to Intersection for Portal, based on relative AD
        0:(0, -1),
        1:(1, 0),
        2:(0, 1),
        3:(-1, 0)
    }
    def getgc(self):
        return Portal.elementwiseadd(self.adjroad.parent.gridcoords, list(Portal.adtoadding[self.position]))
        
    def createped(self):  # basically same as createcar()
        newped = carped.Pedestrian(self)
        #if self.parent.tired == False:
            #newped.strange = True
            #self.parent.tired = True
        self.peds.append(newped)
        
        #return newped

    def releasesome(self):
        # takes at most 1 car and all pedestrians and pushes them into the adjacent road
        if len(self.cars) > 0:
            c = self.cars.pop(0)
            
            success = self.adjroad.offerroad(c)  # if False the Lane must be full
            if not success:
                self.cars.insert(0,c)  # back at the beginning

        # now the pedestrians
        didnotsucceed = []
        for i in range(len(self.peds)):
            success = self.adjroad.offerroad(self.peds[i])
            if not success:
                didnotsucceed.append(self.peds[i])
        self.peds = list(didnotsucceed)  # FIXME this area might break because of pointers

    def deletefinished(self):
        for obj in self.finished:
            if type(obj) == carped.Car:
                self.parent.carsgottenthrough += 1
                self.parent.cummulcartimes += obj.ticksfromspawn
            else:  # Pedestrian
                self.parent.pedsgottenthrough += 1
                self.parent.cummulpedtimes += obj.ticksfromspawn
        del self.finished[:]

    def onetick(self):
        if random.random() < Portal.carprob:
            self.createcar()

        if random.random() < Portal.pedprob:
            self.createped()

        self.deletefinished()  # get rid of cars and peds who were given to the Portal
        self.releasesome()

    def offerportal(self, obj):
        self.finished.append(obj)  # we deal with increasing stuff in MC later
        obj.parent = self  # just because, why not?
        
    carprob = 0.01  # (FON) probability that a car will spawn in a given tick, similar below
    pedprob = 0.01  # (FON)


class MindController:
    # this controls all the interactions of the simulation, aside from the traffic lights
    # does things like make cars move, spawn, etc.

    def __init__(self, s, mode):
        self.sidelength = s  # not including Portals
        self.portals = []  # for easy access
        self.intersections = [[None] * s for _ in range(s)]
        self.initinter(s)
        self.ticks = 0  # time for the simulation; 1 tick is 1/10 a "second"
        
        self.carsgottenthrough = 0  # how many cars got to the other portal so far
        self.pedsgottenthrough = 0
        self.cummulcartimes = 0  # cummulative car times, that is, their ticks since spawns
        self.cummulpedtimes = 0

        self.lightmode = mode  # can be 'n' for neural network, or 'a' for fully automated lights

        self.carspawned = False  # TODO: remove once done debugging
        self.lightvector = None


    '''def findstrange(self):
        for p in self.portals:
            for ped in p.peds:
                if ped.strange:
                    return ped
        for j in self.intersections:
            for i in j:
                for r in i.roads:
                    for ped in r.pedwaiting:
                        if ped.strange:
                            return ped
                for s in i.sidewalks:
                    for ped in s.peds:
                        if ped.strange:
                            return ped
                for z in i.crossings:
                    for ped in z.peds:
                        if ped.strange:
                            return ped'''
                    

    def decidecolor(self, gc):
        if self.lightmode == 'n':
            l = self.intersections[gc[1]][gc[0]].roads[0].light
            lvindex = gc[1]*self.sidelength+gc[0]
            thistickvect = self.lightvector
            newstate = thistickvect[lvindex]
            if newstate >= 0:
                newstate = 1
            else:
                newstate = -1
            newstate = 'g' if newstate == 1 else 'r'
            if l.state != newstate and l.timesince >= Light.mintime:
                l.state = newstate
                l.timesince = 0
            l.timesince += 1
        elif self.lightmode == 'g':
            self.intersections[gc[1]][gc[0]].roads[0].light.state = 'g'  # and the other roads and lights will follow in Road.onetick()
            
    def decidedest(self, p):
        # takes portal and returns a portal which isn't on the same side
        ppos = p.position  # for convenience

        # aside from U-turns, cars never go back the same direction
        # and accuracy regarding destination choice shouldn't matter too much
        diffpos = lambda x: x.position != ppos
        allonothersides = list(filter(diffpos, self.portals))  # filter out portals on the same side as p, including p itself
        dest = random.choice(allonothersides)

        return dest


    @staticmethod
    def printgc(path):
        print('printing gc')
        for p in path:
            print(p.gridcoords)
        print()
    
    def pathfind(self, origin, dest):
        # returns array of intersections to follow, and the portal (for conevnience and corner cases)
        # we notice that since this is a uniform cost grid, a simple right-angle path is the optimal path, tied with several others
        # however, we want to amount of cars flowing through each intersection to be about the same, so we still randomize some of the turns
        # we know that the two portals are not on the same side, so figure out if they are opposite or not
        path = []  # includes Intersections and 1 portal, the destination, does NOT include origin

        ad1, ad2 = origin.position, dest.position
        if (ad1 + 2) % 4 == ad2:  # opposite
            turningpoint = random.choice(range(self.sidelength))  # which row/column to turn on
            if ad1 == 0:
                xval1 = origin.gridcoords[0]  # Intersection's y-val is same as Portal's, since ad == 0, but Portal has no gc, so take from Intersection
                xval2 = dest.gridcoords[0]  # same

                # V TODO: check this for out of index errors
                for y in range(turningpoint + 1):  # we do include turningpoint itself, hence the + 1
                    path.append(self.intersections[y][xval1])  # remember, y comes before x when accessing these thigns

                if xval1 < xval2:
                    for x in range(xval1+1, xval2):
                        path.append(self.intersections[turningpoint][x])
                elif xval2 < xval1:
                    for x in range(xval2-1, xval1, -1):
                        path.append(self.intersections[turningpoint][x])
                # if the xvals equal we do nothing
                    
                for y in range(turningpoint, self.sidelength):
                    path.append(self.intersections[y][xval2])

            elif ad1 == 1:
                yval1 = origin.gridcoords[1]
                yval2 = dest.gridcoords[1]

                # must loop backwards
                for x in range(self.sidelength - 1, turningpoint - 1, -1):
                    path.append(self.intersections[yval1][x])

                if yval1 < yval2:
                    for y in range(yval1+1, yval2):
                        path.append(self.intersections[y][turningpoint])
                elif yval2 < yval1:
                    for y in range(yval2-1, yval2, -1):
                        path.append(self.intersections[y][turningpoint])
                
                for x in range(turningpoint, -1, -1):  # oneday I am going to make a clone of Python3 where the only thing different is how for loops work.
                    path.append(self.intersections[yval2][x])
            elif ad1 == 2:
                xval1 = origin.gridcoords[0]
                xval2 = origin.gridcoords[0]

                for y in range(self.sidelength - 1, turningpoint - 1, -1):
                    path.append(self.intersections[y][xval1])

                if xval1 < xval2:
                    for x in range(xval1+1, xval2):
                        path.append(self.intersections[turningpoint][x])
                elif xval2 < xval1:
                    for x in range(xval2-1, xval1, -1):
                        path.append(self.intersections[turningpoint][x])
                    
                for y in range(turningpoint, -1, -1):
                    path.append(self.intersections[y][xval2])
            else:  # ad1 == 3
                yval1 = origin.gridcoords[1]
                yval2 = dest.gridcoords[1]

                for x in range(turningpoint + 1):
                    path.append(self.intersections[yval1][x])

                if yval1 < yval2:
                    for y in range(yval1+1, yval2):
                        path.append(self.intersections[y][turningpoint])
                elif yval2 < yval1:
                    for y in range(yval2-1, yval2, -1):
                        path.append(self.intersections[y][turningpoint])
                
                for x in range(turningpoint, self.sidelength):
                    path.append(self.intersections[yval2][x])
            
        elif (ad1 + 1) % 4 == ad2:  # 'left'
            if ad1 == 0:
                for y in range(dest.gridcoords[1]):  # not +1 becausae that's covered in the next loop
                    path.append(self.intersections[y][origin.gridcoords[0]])
                for x in range(origin.gridcoords[0], self.sidelength):
                    path.append(self.intersections[dest.gridcoords[1]][x])
            elif ad1 == 1:
                for x in range(self.sidelength - 1, dest.gridcoords[0], -1):
                    path.append(self.intersections[origin.gridcoords[1]][x])
                for y in range(origin.gridcoords[1], self.sidelength):
                    path.append(self.intersections[y][dest.gridcoords[0]])
            elif ad1 == 2:
                for y in range(self.sidelength - 1, dest.gridcoords[1], -1):
                    path.append(self.intersections[y][origin.gridcoords[0]])
                for x in range(origin.gridcoords[0], -1, -1):
                    path.append(self.intersections[dest.gridcoords[1]][x])
            else:
                for x in range(dest.gridcoords[0]):
                    path.append(self.intersections[origin.gridcoords[1]][x])
                for y in range(origin.gridcoords[1], -1, -1):
                    path.append(self.intersections[y][dest.gridcoords[0]])
        else:  # 'right'
            if ad1 == 0:
                for y in range(dest.gridcoords[1]):
                    path.append(self.intersections[y][origin.gridcoords[0]])
                for x in range(origin.gridcoords[0], -1, -1):
                    path.append(self.intersections[dest.gridcoords[1]][x])
            elif ad1 == 1:
                for x in range(self.sidelength - 1, dest.gridcoords[0], -1):
                    path.append(self.intersections[origin.gridcoords[1]][x])
                for y in range(origin.gridcoords[1], -1, -1):
                    path.append(self.intersections[y][dest.gridcoords[0]])
            elif ad1 == 2:
                for y in range(self.sidelength - 1, dest.gridcoords[1], -1):
                    path.append(self.intersections[y][origin.gridcoords[0]])
                for x in range(origin.gridcoords[0], self.sidelength):
                    path.append(self.intersections[dest.gridcoords[1]][x])
            else:  # ad1 == 3
                for x in range(dest.gridcoords[0]):
                    path.append(self.intersections[origin.gridcoords[1]][x])
                for y in range(origin.gridcoords[1], self.sidelength):
                    path.append(self.intersections[y][dest.gridcoords[0]])

        path.append(dest)  # because it goes here too
        path = list(OrderedDict.fromkeys(path))  # in the special case that origin and dest are *directly* opposite each other, this removes the duplicate intersection
        #if MindController.allclose(path) == False:
        #    import pdb; pdb.set_trace()
        #    self.pathfind(origin, dest)
        
        return path

    @staticmethod
    def close(x,y):
        gc1 = x.gridcoords
        gc2 = y.gridcoords
        if [abs(gc1[0]-gc2[0]), abs(gc1[1]-gc2[1])] in [[0,1],[1,0]]:
            return True

    @staticmethod
    def allclose(path):
        for i in range(len(path)-1):
            if not MindController.close(path[i], path[i+1]):
                return False
        return True
    def initinter(self, s):
        for y in range(s):  # y goes top to bottom
            for x in range(s):  # x goes left to right
                self.intersections[y][x] = concrete.Intersection([x,y], self)

        # need to do this twice (^) to set the adjacent property
        for y in range(s):
            for x in range(s):
                inter = self.intersections[y][x]
                coords = [[x, y-1], [x+1, y], [x, y+1], [x-1, y]]

                for adjcoord in coords:
                    a = adjcoord[0]  # abbreviation
                    b = adjcoord[1]

                    if (not a in range(s)) or (not b in range(s)):  # then we create a portal
                        road = inter.roads[MindController.directiontotake([x,y], [a,b])]

                        portalpos = coords.index([a, b])
                        portal = Portal(road, portalpos, self)
                        inter.adjacents[portalpos] = portal
                        self.portals.append(portal)
                    else:
                        inter.adjacents[coords.index([a, b])] = self.intersections[b][a]

    @staticmethod
    def directiontotake(currgc, nextgc):
        x1, x2, y1, y2 = currgc[0], nextgc[0], currgc[1], nextgc[1]
        if x1 < x2:
            return 1
        elif x1 > x2:
            return 3
        elif y1 < y2:
            return 2
        else:  # y1 > y2
            return 0

    def onetick(self):  # does everything that happens in a single tick
        # (almost?) every object has has a similar function which is called by this one
        # spawn and release cars, make everything move forwards, increments waiting counters, etc.
        self.ticks += 1
        if self.ticks >= 10000:
            self.ticks = 10001
            return
        for i in self.intersections:
           for j in i:
               self.decidecolor(j.gridcoords)
        for p in self.portals:
            p.onetick()

        for i in self.intersections:
            for j in i:
                j.onetick()

    tired = False
