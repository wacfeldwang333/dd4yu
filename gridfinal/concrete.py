# Intersection, Road, Lane, Middle - big infrastructure stuff

import carped, virtual
import math, random


class Intersection:
    # an intersection consists of 4 roads and a middle; everything else is contained inside the roads
    # intersections do NOT have roads leading out of them, only in
    # once a car goes through, it immediately transfers to the next intersection

    # whichroads is a string of 4 1s and 0s telling you what roads are active, going clockwise
    # note that an inactive road is not necessarily an edge road, since the edges typically have roads for the portals
    # adj always is a tuple of 4 since if it's on the edge it has portals
    def __init__(self, gc, p):
        self.adjacents = [None] * 4  # intersections/portals adjacent to this intersection
        self.parent = p
        self.gridcoords = gc  # used by MindController.pathfind() to figure out where it's located on the grid
        self.middle = Middle(self)

        # initiates roads
        # roads are ordered clockwise, starting from top
        self.roads = []
        for i in range(4):
            newroad = Road(self, i)
            self.roads.append(newroad)

        r1, r2, r3, r4 = self.roads[0], self.roads[1], self.roads[2], self.roads[3]  # for ease of use
        self.crossings = [r1.crossing, r2.crossing, r3.crossing, r4.crossing]

        # set the sidewalks
        s1 = virtual.Sidewalk(self, r1.crossing, r2.crossing)  # upper right corner
        s2 = virtual.Sidewalk(self, r2.crossing, r3.crossing)  # bottom right corner
        s3 = virtual.Sidewalk(self, r3.crossing, r4.crossing)  # etc, clockwise
        s4 = virtual.Sidewalk(self, r4.crossing, r1.crossing)
        self.sidewalks = [s1, s2, s3, s4]

        # set the road's sidewalk attributes, for Intersection.gettargetsidewalk()
        r1.sw1, r1.sw2 = s4, s1  # top
        r2.sw1, r2.sw2 = s1, s2  # right
        r3.sw1, r3.sw2 = s2, s3  # etc clockwise
        r4.sw1, r4.sw2 = s3, s4

        for r in self.roads:
            r.crossing.setsidewalks()

    mapping = {(0,2):1, (1,3):1, (2,0):1, (3,1):1, (0,3):2, (1,0):2, (2,1):2, (3,2):2, (0,1):0, (1,2):0, (2,3):0, (3,0):0}  # left, forward, right = 0, 1, 2
    
    @staticmethod
    def getrelativedirection(facing, ad):
        # facing is the orientation of the road
        # ad is the absolute direction the car should move
        return Intersection.mapping[(facing,ad)]

    def onetick(self):
        r0, r1, r2, r3 = self.roads[0], self.roads[1], self.roads[2], self.roads[3]
        if r0.light.state == 'r':
            r0.light.state = 'y'
            r0.light.yellowtimeleft = virtual.Light.yellowtime
        r2.light.state = r0.light.state
        
        if r0.light.state == 'g':
            if r1.light.state == 'g':
                r1.light.state = 'y' if r0.light.state == 'g' else 'g'
                r2.light.state = r1.light.state
                r1.light.yellowtimeleft = virtual.Light.yellowtime
                r3.light.yellowtimeleft 
            elif r1.light.state == 'y':
                r1.light.yellowtimeleft -= 1
                if r1.light.yellowtimeleft <= 0:
                    r1.light.state == 'r'
                    r1.crossing.pedlight.state == 'r'
                    r3.crossing.pedlight.state == 'r'
                    r3.light.state == 'r'

        elif r0.light.state == 'y':
            r0.light.yellowtimeleft
            r0.light.yellowtimeleft -= 1
            if r0.light.yellowtimeleft <= 0:
                r0.light.state = 'r'
                r1.light.state = 'g'
        r3.light.state = r1.light.state
        # if it's red already we don't need to do anything
        for r in self.roads:
            r.onetick()
        for s in self.sidewalks:
            s.onetick()
        for zc in self.crossings:
            zc.onetick()
        self.middle.onetick()

    def getoppositeroad(self, r):  # used to get the light which controls the opposite road
        ad = r.absolutedir
        return self.roads[(ad + 2) % 4]


class Road:
    # note that intersections at the edge still have 4 roads (0 or 1 or 2 are technically Portals)

    def __init__(self, p, ad):
        self.rc = self.getlens()  # respective capacities

        self.absolutedir = ad  # the way the road is facing based off the whole grid
        self.parent = p
        self.left = Lane(0, self, self.rc[0])
        self.forward = Lane(1, self, self.rc[1])
        self.right = Lane(2, self, self.rc[2])
        self.lanes = [self.left, self.forward, self.right]

        self.middle = self.parent.middle

        self.sw1 = None  # initialized by Intersection after Sidewalks are made
        self.sw2 = None  # ordered RTL, facing Middle
        self.crossing = virtual.ZebraCrossing(self)  # placed here for easy access from cars
        self.pedwaiting = []  # pedestrians wait before moving to sidewalk

        self.light = virtual.Light(self)  # note that lights control the opposite road, not the one they belong to!

        self.speedlimit = random.choice(Road.potentialspeedlimits)
        self.length = 20

    potentialspeedlimits = [11.11, 13.88, 16.66]  # either 40, 50, or 60 km/h, or 11.11, 13.88, 16.66 m/s
    
    @staticmethod
    def decidelength():
        return 30
    
    @staticmethod
    def getlens():  # length in meters of all three lanes, random
        return [30,30,30]

    # TODO: make the car figure out the next Lane to go to while in the previous intersection
    def offerroad(self, obj):  # something tries to give road a ped or car from adjacent portal or intersection
        # if failed the Portal/Middle keeps it
        # named this way to avoid confusion - Road is being given object
        #obj.parent = self

        if type(obj) is carped.Car:
            if obj.lanetoenter == None:  # then figure that out, this is kept if the car is rejected
                currgc = self.parent.gridcoords
                if obj.path[0] != self.parent:
                    obj.path.insert(0, self.parent)
                nextgc = obj.path[1].gridcoords  # intersection after this one in Pedestrian's path
                
                absolutedirection = virtual.MindController.directiontotake(currgc, nextgc)  # up, right, down, left -> 0, 1, 2, 3

                reldir = Intersection.getrelativedirection(self.absolutedir, absolutedirection)
                obj.path = list(obj.path[1:])
                
                obj.lanetoenter = self.lanes[reldir]

            if obj.lanetoenter.carcanenter():
                # set the variables in Car
                obj.parent = obj.lanetoenter
                obj.position = obj.lanetoenter.length  # very end of the lane
                if len(obj.lanetoenter.cars) != 0:
                    #if obj.lanetoenter.cars[-1].speed == None:
                        #print(len(obj.lanetoenter.cars))
                    obj.speed = obj.lanetoenter.cars[-1].speed  # set speed to that of next car
                    #print(obj.speed)
                    #print('hi!')
                else:
                    obj.speed = obj.lanetoenter.parentroad.speedlimit
                obj.lanetoenter = None  # reset for later

                obj.parent.cars.append(obj)
                
                #if len(obj.parent.cars) == 1:
                    #print(obj.speed)
                    #print('\n\n\n\n\n')
                return True  # operation succeeded, car entered

        elif type(obj) is carped.Pedestrian:  # always accept it, then
            obj.parent = self
            obj.currtarzc = None
            currgc = self.parent.gridcoords
            if obj.path[0] != self.parent:
                obj.path.insert(0, self.parent)  # a terrible way to fix a bug that will probably break but i've been attacking this for the past 5 days and just don't care anymore TODO fix this hackishh soluution that some idiot wrote up (as iin, after science fair is over, in 5 years just look at thhis and see the solution immediately)


            nextgc = obj.path[1].gridcoords
            
            obj.path = list(obj.path[1:])  # we are done with this

            
            absolutedirection = virtual.MindController.directiontotake(currgc, nextgc)
            reldir = Intersection.getrelativedirection(self.absolutedir, absolutedirection)
            
            #obj.pathrecord.append(list(obj.path))
            
            if reldir == 0:
                obj.currtarsw = self.sw2
            elif reldir == 1:
                obj.currtarsw = self.sw2  # Ontario recommends you walk on the left, for some reason
            elif reldir == 2:
                obj.currtarsw = self.sw1
                
            obj.walkingtimeleft = obj.timeleft(self.length)

            self.pedwaiting.append(obj)

            return True  # operation succeeded

        return False

    def onetick(self):
        # decide light color
        
        # call onetick() on all lanes and decrease Pedestrian wait time
        for l in self.lanes:
            l.onetick()

        stayedinroad = []
        for p in self.pedwaiting:
            p.ticksfromspawn += 1
            p.walkingtimeleft -= 1
            if p.walkingtimeleft <= 0:  # then move it to currtarsw
                p.walkingtimeleft = None
                p.parent = p.currtarsw

                p.currtarsw.peds.append(p)
                
                p.currtarsw = None  # have to decide this later
                p.justgothere = True
            else:
                stayedinroad.append(p)
        self.pedwaiting = list(stayedinroad)


class Lane:
    def __init__(self, d, parent, c):
        self.cars = []  # first in the array are closest to middle of intersection
        self.direction = d  # direction is l, r, or f
        self.parentroad = parent
        self.bigbrother = self.parentroad.parent
        self.length = c

    lanewidth = 3.5  # meters
    
    def isopen(self, targetroad):  # checks ZCs, Lights, etc. to see if car can go this way
        # note this tells you whether a car can drive FROM this lane, not to
        if targetroad.crossing.occupied or self.crossing.occupied:
            return False
        # TODO: check middle of intersection with predictions of where cars will be in the future

    def carcanenter(self):  # if a car in Road.offerroad()
        if len(self.cars) != 0:
            lastcar = self.cars[-1]
            if lastcar.position + carped.Car.calcbuffer(lastcar.speed) > self.length:
                return False
        return True

    def onetick(self):
        # go through cars, based on reaction delays, speeds, etc. move them accordingly
        stayedinlane = []  # as in, didn't go to the middle, the ones we keep
        currgc = self.bigbrother.gridcoords
        for c in self.cars:
            nextgc = c.path[0].gridcoords  # FIXME: should the index be 0 or 1?
            ad = virtual.MindController.directiontotake(currgc, nextgc)  # absolute direction, tells us the next intersection to take
            nextroad = self.bigbrother.roads[ad]  # car doesn't drive on this road; it drives on the adjacent road on the next intersection
            #if c.middlepath == None:  # it just entered the lane, decide its path through the middle
                #c.middlepath = self.bigbrother.middle.getpath(c, self, ad)
            c.ticksfromspawn += 1

            notexec = []  # not executed, as in not run
            for r in c.reactiondelay:
                r[0] -= 1  # decrement the reaction time
                # ^ TODO: will this break because of pointers?

                if r[0] == 0:
                    c.run(r[1])  # run the command
                else:
                    notexec.append(list(r))
            del c.reactiondelay[:]  # delete everything...
            c.reactiondelay = notexec  # ... and replace it with the ones that haven't been executed

            c.middlepathclear = True  # otherwise the results from last tick will go over and mess everything up
            # figure out what situation the car is in right now
            if self.cars.index(c) == 0:  # front of the Lane
                # if it's at the front we check for obstacles in the middle every tick instead of every 10
                # if this crossing or nextroad.crossing occupied, brake completely, same if red light and not right turning, if yellow light, determine based on c.position and c.speed
                self.checkconditions(c, nextroad)  # decides middlepathclear
                # deal with changing speed
                if c.middlepathclear:
                    if self.direction in ['l', 'r']:  # then speed should decrease to 1/2 of speed limit
                        c.targetspeed = self.parentroad.speedlimit / 2
                    else:
                        c.targetspeed = self.parentroad.speedlimit
                    c.reactiondelay.append([carped.Car.reactivity, 'self.changespeedlinear()'])
                else:  # road is not clear
                    # decreasing logarithmically
                    c.reactiondelay.append([carped.Car.reactivity, 'self.setdecelspeed()'])
                    
            else:  # not first car
                # notice how the middle has already been checked by the car in front since they're turning the same way
                # make sure no collisions
                carinfront = self.cars[self.cars.index(c) - 1]  # the car closer to the Middle
                higherspeed = max([carinfront.speed, c.speed])  # use this to calculate the buffer
                #if c.position - carinfront.position - carped.Car.length - carped.Car.calcbuffer(higherspeed) <= 0:  # if the cars are too close
                    # this should NEVER happen, so print to console
                    #print('Dude, I hate to break it to you, but it\'s debugging time. We cannot have car crashes!')
                    #exit(0)  # TODO: remove this all once debugging is done. No, not the whole project, just these few lines.
                
                # with reactiondelay, set speed of car to that of car in front
                comm = 'self.speed = ' + str(round((carinfront.speed + c.speed) / 2))
                c.reactiondelay.append([carped.Car.reactivity, comm])  # set this to be executed when the driver 'reacts'

            c.position -= c.speed / 10
            if c.position <= 0.5 and c.middlepathclear == False:  # then round to 0, set speed to 0 as well, to avoid Arrow Paradox!
                c.position = 0
                c.speed = 0
                
            # put car into middle if fitting requirements
            if c.position <= 0 and self.parentroad.middle.pathisclear(self):  # go into Middle
                # we let Middle deal with directions and fun stuff, here we just dump it
                self.parentroad.middle.offermiddle(c)
            else:
                stayedinlane.append(c)

        self.cars = list(stayedinlane)  # get rid of the traitors who left us for the middle
        del stayedinlane

    def checkconditions(self, c, nr):
        nextroad = nr
        oppositelight = self.bigbrother.getoppositeroad(self.parentroad).light
        if self.parentroad.crossing.occupied or nextroad.crossing.occupied:  # one of two crossings is occupied
            c.middlepathclear = False
        elif oppositelight.state == 2:  # red
            if self.direction != 'r':
                c.middlepathclear == False
            # right turning cars will NEVER crash in the middle due to the simulation layout
        elif oppositelight.state == 1:  # yellow
            # figure out whether to decelerate or keep going
            if c.goingthroughyellow == False:
                c.middlepathclear == False
            elif c.goingthroughyellow == None:  # then based off c.position decide whether to go through
                if self.direction == 'r':
                    c.goingthroughyellow = True
                elif (c.position + (Middle.leftturninglength if self.direction == 'l' else Middle.forwardturninglength)) / c.speed < oppositelight.yellowtimeleft - 0.5:  # the logic here is you want to get through the Middle in less than the time left for yellow
                    # ^ TODO: figure out which are ticks and which are seconds and fix
                    c.goingthroughyellow = True
                elif self.direction != 'r':
                    c.goingthroughyellow = False
        # if it's green we do nothing
        if not self.bigbrother.middle.pathisclear(self):
            c.middlepathclear = False

class Middle:
    # the middle of the intersection; split up into nxn squares
    # n must be even to evenly split up the roads leading in and out
    # certain square are special; e.g. some are places a car can leave or enter an intersection

    def __init__(self, parent):
        self.parent = parent
        self.cars = []
        # redundand? - self.occupiedpoints = []  # array of points that cars or their buffer occupy at this instant
        # also redundant? - self.tobeoccupied = []  # matrix of points that cars are going to occupy
        # ^ used with Car.position to decide right of way

    # V redundant?
    sidelength = 64  # not 60 so that we don't get out of index errors. Screw good practice. I'm lazy.
    # ^ no particular unit
    lengthinmeters = 30  # data taken from Victoria, Fischer Hallman intersection
    leftturninglength = (math.pi * 0.5 * (35/60) * lengthinmeters) * 0.5
    forwardturninglength = 60 * 0.5
    rightturninglength = (math.pi * 0.5 * (5/60) * lengthinmeters) * 0.5
    # may be redundant, who knows?
    # rightmapping = {
    #     0:[[-30,30], [-25,-30], [-30,-25]],
    #     1:[[30,30], [30,25], [25,30]],
    #     2:[[30,-30], [25,-30], [30,-25]],
    #     3:[[-30,-30], [-30,-25], [-25,-30]]
    # }
    # leftmapping = {
    #     0:[[30,30], [-5,30], [30,-5]], 1:[[30,-30], [30,5], [-5,-30]], 2:[[-30,-30], [5,-30], [-30,5]], 3:[[-30,30], [-30,-5], [5,30]]
    # }  # used in Middle.getpath()
    # forwardmapping = {0:[[-15,30], [-15,-30]], 1:[[30,15], [-30,15]], 2:[[15,-30], [15,30]], 3:[[-30,-15], [30,-15]]}
    # # ^ format is pivot (if necessary), start, end
    # # may continue to use because of start and end coords
    # # the one below does degrees

    '''angleinterval = 1  # how many degrees to move each time while turning in Middle
    rightlen = 5  # radius of right turning circle
    rightmapping = {
        0:((-30,30), 0, 270, -1),  # last element is the step, in this case it goes backwards
        1:((30,30), 270, 180, -1),
        2:((30,-30), 180, 90, -1),
        3:((-30,-30), 90, 0, -1)
    }
    leftlen = 25  # radius of left turning circle
    leftmapping = {
        0:((30,30), 180, 270, 1),
        1:((30,-30), 90, 180, 1),
        2:((-30,-30), 0, 90, 1),
        3:((-30,30), 270, 0, 1)
    }  # used in Middle.getpath()
    # ^ format is pivot, start, end
    forwardmapping = {  # format is start, end, which value changes, direction to change
        0:((-15,30), (-15,-30), 1, -1),
        1:((30,15), (-30,15), 0, -1),
        2:((15,-30), (15,30), 1, 1),
        3:((-30,-15), (30,-15), 0, 1)
    }'''

    #notnone = lambda x: x != None
    '''def getpath(self, c, lane, targetad):
        # note that targetad is the ad relative to THIS intersection, not the next in path
        # first figure out straight line or curved
        path = []
        currad = lane.parentroad.absolutedir

        tempcoord = None
        if (currad + 2) % 4 == targetad:  # straight line
            info = list(Middle.forwardmapping[currad])
            which = info[2]
            for i in range(info[0][which], info[1][which] + 1, info[3]):
                tempcoord = list(info[0])
                tempcoord[which] += i
                path.append(tempcoord)
        elif (currad + 1) % 4 == targetad:  # left, big circle
            info = list(Middle.leftmapping[currad])
            pivot = list(info[0])
            for a in range(info[1], info[2], info[3]):  # iterates through angles
                r = Middle.leftlen
                path.append([pivot[0] + r * math.cos(a),  pivot[1] + r * math.sin(a)])  # get next point on circle
        else:  # right, little circle
            
            info = list(Middle.rightmapping[currad])
            pivot = list(info[0])

            r = Middle.rightlen
            middlea = (info[1] + info[2])/2
            path.append([pivot[0] + r*math.cos(middlea), pivot[1] + r*math.sin(middlea)])
            print('hi')
            print(pivot[0])
            print(pivot[1])
            #for a in range(info[1], info[2], info[3]):
            #    print('hello!')
            #    r = Middle.rightlen
            #    path.append([pivot[0] + r * math.cos(a),  pivot[1] + r * math.sin(a)])
            #    print('appended ' + str(path[-1]))
            #print('all in all, ' + str(path))
            print(path)
        path = list(filter(Middle.notnone, path))  # another incredibly hackish way to fix it, I DON'T CARE AND I HAVE DEADLINES COMNING UP
        #print('path is ' + str(path) + '\n'*5)
        #print('\n\n\n')
        #print('again, ' + str(path))
        return path'''
        
    pathcrossmapping = {
        0:'f',
        1:'l',
        2:None  # point is, no character will equal this, since right turning cars are never an obstacle
    }
    def pathisclear(self, prevparent):  # check if its path crosses anything else
        # called by a car in Lane, going to enter Middle
        # here is why we constantly delete elements in Car.middlepath, to see onle where the cas is going to be, not where it was
        # we make prevparent an argument so we can check this while the car is still in the lane
        cad = prevparent.parentroad.absolutedir  # use to compare to other cars' ADs
        cturning = prevparent.direction
        for potobst in self.cars:  # check their prevparents to see the direction they are taking, and the orientation
            # ^ stands for potential obstacle
            otherad = potobst.prevparent.parentroad.absolutedir
            if (cad + 2) % 4 == otherad and Middle.pathcrossmapping[cturning] == potobst.prevparent.direction:  # if they are on opposite roads and they are turning the right (wrong?) way
                return False
        # otherwise they must be either turning right or stopped, so no problem
        return True

    '''@staticmethod
    def calcdist(c1, c2):  # used in Middle.onetick()
        if c1[0] == c2[0]:
            return math.abs(c1[1] - c2[1])
        elif c1[1] == c2[1]:
            return math.abs(c1[0] - c2[0])
        else:
            return math.sqrt((c1[0] - c2[0]) ** 2  +  (c1[1] - c2[1]) ** 2)  # Pythag. Thm.'''

    '''rightsmalldist = 2 * math.pi * rightlen * (angleinterval/7) / 360  # distance between two points in c.path for right turning car
    # ^ divide angle interval by seven because the turning is smaller
    leftsmalldist = 2 * math.pi * leftlen * angleinterval / 360  # similar
    forsmalldist = 1  # also similar'''
    def onetick(self):
        stayedinmiddle = []
        for c in self.cars:
            c.ticksfromspawn += 1
            c.changespeedlinear()

            # TODO: check for obstacles in path
            
            # deal with actually moving now
            dirturning = c.prevparent.direction  # 'l', 'r', 'f'
            c.disttraveledinmid += c.speed / 10  # in ticks, remember!

            totalturninglen = Middle.leftturninglength if dirturning == 'l' else (Middle.rightturninglength if dirturning == 'r' else Middle.forwardturninglength)
            if c.disttraveledinmid >= totalturninglen:  # then we DON'T want to get stuck in an infinite loop so STOP THIS MADNESS I should probably not listen to music while working
                if type(c.path[0]) is virtual.Portal:  # then we simply give it to the Portal, without all the complicated stuff
                    c.path[0].offerportal(c)
                else:
                    roadad = virtual.MindController.directiontotake(c.path[0].gridcoords, self.parent.gridcoords)  # note how the GCs are reversed, since we are getting the ROAD, which is opposite the actual GC
                    nextroad = c.path[0].roads[roadad]
                    nextroad.offerroad(c)
                continue  # DON'T GET STUCK IN AN INFINITE LOOP
            else:
                stayedinmiddle.append(c)
            
            '''for i in range(len(c.middlepath) - 1):  # ignore the last
                disttraveledinloop += Middle.calcdist(c.middlepath[i], c.middlepath[i + 1])
                if math.abs(disttraveledinloop - c.disttraveledinmid) < (Middle.rightsmalldist if dirturning == 'r' else (Middle.leftsmalldist if dirturning == 'l' else Middle.forsmalldist)):  # if the error is smaller small enough to ignore
                    c.coords = c.middlepath[i + 1]
                    del c.middlepath[:i+1]  # remove redundant stuff
                    break'''
        self.cars = list(stayedinmiddle)
        del stayedinmiddle
            
    def offermiddle(self, c):
        # we always accept it because it's been checked beforehand
        c.prevparent = c.parent  # need this later

        c.parent = self
        self.cars.append(c)
        '''c.coords = c.middlepath[0]'''
        c.position = None
        c.disttraveledinmid = 0

        speedlimit = c.prevparent.parentroad.speedlimit
        rd = c.prevparent.direction  # which way the car is turning
        if rd in ['l', 'r']:  # then adjust to a lower speed, go 1/3 of speed limit of previous road
            c.targetspeed = speedlimit / 3
        else:  # approach speed limit
            c.targetspeed = speedlimit
