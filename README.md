# ddy4yu
Some of Daniel Yu's code. Details listed below.

## Netflix Ratings (folder chrome-extension) - c. June 2018 (grade 9)
- Language: Javascript/HTML
- A Chrome extension for Netflix, which detects when the user hovers over a thumbnail, searches Google for the movie/show, and displays its rating next to the thumbnail.

## MITON (folder name gridfinal) - c. Feb-Mar 2018 (grade 9)
- Language: Python 3.
- a.k.a. Multi-Intersection Traffic Optimization Using Neural Networks. Keras was used for the neural networks, but everything else was done from scratch.
- Won a gold medal at WWSEF 2018.
- carped.py defines the classes Car and Pedestrian, which drive and walk in the simulation.
- concrete.py defines classes Intersection, Road, Lane, Middle (the square in the middle of the intesection).
- draw.py was not used.
- graphics.py was not mine, but was also not used.
- main.py runs the simulation, controlling traffic light using the neural network. It measures the efficiency and trains the network.
- rnntest.py was unused.
- virtual.py defines classes ZebraCrossing, Sidewalk, Portal (each Car/Pedestrian is spawned at one Portal, then drives/walks to another Portal, and is destroyed, akin to entering and leaving a group of intersections), MindController (which spawns/destroys Cars/Pedestrians, makes them start, accelerate, stop, etc.).
- saves/ contains various generations of the neural network, as well as a graph of the network's improvement over time.
- Trained for approximately 12 hours.


## Quine - date unknown
- Two Quine programs that print their own source code
- quine.cpp does not seem to work, but quine.py does.
