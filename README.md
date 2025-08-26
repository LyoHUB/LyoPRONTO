
LyoPRONTO is an open-source user-friendly tool to simulate and optimize freezing and primary drying in lyophilizers written using Python.

# Authors
Original authors: Gayathri Shivkumar, Petr S. Kazarin and Alina A. Alexeenko.
Maintained and updated by Isaac S. Wheeler.

# Interactive Simulation
A web-based GUI is available for this software at http://lyopronto.geddes.rcac.purdue.edu.

# How to Use This Code Directly
Download this repository, then in your preferred command line navigate to the containing directory (so that `LyoPronto` is a subdirectory).
Execute:
```
python3 LyoPronto.main -m
```
This will execute the file `main.py` in an appropriate scope. Parameters can be changed in `main.py`. Files listing the inputs and outputs will be generated in the current directory, along with some plots of temperature, pressure, and drying progress vs. time.
A video tutorial by the authors illustrating this process can be found [on LyoHUB's YouTube channel](https://youtu.be/DI-Gz0pBI0w).

# Citation
G. Shivkumar, P. S. Kazarin, A. D. Strongrich, & A. A. Alexeenko, "LyoPRONTO: An Open-Source Lyophilization PRocess OptimizatioN TOol",  AAPS PharmSciTech (2019) 20: 328. 

The noted paper is open access, and can be found [here](https://link.springer.com/article/10.1208/s12249-019-1532-7).

# Licensing

Copyright (C) 2019, Gayathri Shivkumar, Petr S. Kazarin and Alina A. Alexeenko.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

By request, this software may also be distributed under the terms of the GNU Lesser General Public License (LGPL); for permission, contact the authors or maintainer.

# Notes on contributing & maintenance

There is a GitHub Action on this repo which will automatically build the documentation (which uses Material for MkDocs with `mike` for versioning). This action triggers on push to main (which creates a `dev` section of the docs), on publishing a release (which creates a numbered version of the docs), and on pull request edits (which makes a `pr-###` version of the docs). 
After merging a pull request, it is a good idea to use [mike](https://github.com/jimporter/mike) to clear out the PR version of the docs. Locally, do something like the following
```
git fetch 
mike delete pr-### # replace with correct PR number
git switch gh-pages
git push origin gh-pages
```
This could theoretically be automated but I decided against this for now. In the long run, it may be worth not generating PR versions of the docs if this is burdensome.