# path_analysis_hw
I'm sitting next to a multi-ton, 6dof, Kuka robot arm. It's not doing what I want it to do.

The robot takes in a list of points and do their best to go to those points in order. The thing is, I just did that and the robot didn't look right. For instance, there is a section of the path I sent to the robot that is a bunch of circles, and instead of tracing out circles, the robot just sat there unmoving... Something definitely isnt right. 

## The ask
Here's where you come in. I want to know why the robots didn't follow my instructions. Fortunately for us, I managed to save some logs during the run:
 - path.csv These are the points I told the robot to go to. Generally, a bunch of loops in the xy plane. 
 - tracker.csv This is where the robot went as measured by some optical trackers. 

Your task: generate insights. The more graphs and sick visualizations, the better. Generally, what parameters of the input points correlate with error? 

## A word of caution about those logs...
 - The tracker points are logged in the tracker coordinates. No idea what the transform is between those and the coordinates of the path. Fortunately, I threw in some "registration points" at the top of the path. Maybe those can help.
 - Due to some clock desynchrony, it appears that the time stamps in tracker.csv might be shifted from the time stamps in path.csv. Consider it pretty close, but I'm all ears if you can think of a way to handle that. 
 - The data here likely is likely insufficient. Do your best, and document your assumptions along the way. 

May the wind fill your sails, and godspeed.
