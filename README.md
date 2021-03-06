# Aillio Bullet R1, powered by _Ballistics_

I wanted to process all the data that the RoasTime and Roast.World collects about all 
the coffee roasting.
I wrote this module to automatically do some calculations, generate labaels and upload 
it all to my Headless CMS that feeds my website. 

## Configuration
Create `.env` file for all the local configuration settings.

See `.env.example` for details on what options are available.

_TODO_:
- Add roast level to the label
- Consider iterating on all environment variables beginning with 'BALL_' and auto
processing those into the environment

## Applications
Here are the applications in use in this repo that make use of the proto-module "ballistics".

### Batch Process (`process_all.py`)
This processes all the beans and roasts into an output directory 

_TODO_:
- initial commit
- generate some kind of report on bean quantities/usage

### Load One (`load_one.py`)
This loads one roast, for quick checking and debugging.
Design to be run in an interactive shell so that the loaded objects (and raw JSON) 
can be explored interactively.

_TODO_:
- take runtime args for which roast (by number, name?)

## Ballistics Module
This is where I have wrapped up the module with some utility programs.

### Classes
#### Bean

_Attributes_:
- list TBC
- raw: the raw JSON file loaded from RoasTime
- roasts: a list of roastIds that use this bean

#### Roast

_Attributes:_
- list TBC
- raw: the raw JSON file loaded from RoasTime

_Functions:_
- find_roast_by: find roasts by partial match on name or beanId if 'beanid' flag is set

#### RoastCollection
A collection of Roast objects

_Attributes:_
- roasts: a list of Roast objects

## TODO:

#### Ballistics Module:
- There are many things to do!
- Additional commentary from other sources to be brought in and added to the Contentful
content
- Make up labels in two sizes, at high resolution
- Save to md/Contentful/other
- generate profile graph

#### Applications
- There are many things to do!
- .env.placeholder to show all the options that can be overridden
- Cupping scores
- Reviews from drinkers
- Aggregate scores from roasts to the bean as a whole
- Tasting notes (keyword tagging a la Untapped?)
- Assembling blend recipes, harking to the component beans

## Releases
Target for first release
