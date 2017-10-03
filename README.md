# pyApex
Apex Project BIM Utils - an extension for [pyRevit](http://eirannejad.github.io/pyRevit/)

![Preview image](https://raw.githubusercontent.com/apex-project/pyApex/master/preview.png)

## Features

1. Selection

- Open Views - opens all selected views

- Select Many IDs - select elements by text pasted from Warnings Reports

- Zoom Base Point

2. Model

- Change Level - remove selected level and transfer all its object to another selected level

- Level Dependence - show elements dependen of selected levels

- Unjoin Selected - unjoin all selected geometry

- Unjoin Warnings - unjoin elements by pasted text from Warnings Reports

3. Detail

- Copy VG Filters - copying filter from one view template to others

- Text Notes 2 CSV - finds text notes on selected views and saves it's content to csv

4. Misc

- SheetsEnum - enumerate selected sheets (WIP)

- White Materials - useful for render. Change all material appearance to white and back. Exceptions are WIP.

- Objects on Worksets - show list of objects which belongs to selected workset. Useful to check before deleting the workset.

- Worksets for links - create worksets for all types of links.

- Purge recursively - open each family and purge its content recursively

- Select duplicate tags


## Installation

1. Download and install pyRevit from http://eirannejad.github.io/pyRevit/

2. Add this text to pyRevit extension.json at your pyrevit installation ( pyRevit\\extensions )

```
,{
"builtin": "False",
"enable": "True",
"type": "extension",
"name": "pyApex",
"description": "Apex Project BIM Utils",
"author": "APEX Project",
"author-url": "https://github.com/apex-project/",
"url": "https://github.com/apex-project/pyApex.git",
"website": "https://github.com/apex-project/pyApex",
"image" : "",
"dependencies": []
}
```

3. Add pyApex extension by Extension button http://eirannejad.github.io/pyRevit/sharingextensions/

## Contribution

Feel free to report about bugs to issues tab. 

You're also welcome to make any contributions - add comments, fork and make pull-requests. With any ideas write to aleksey.melnikov@apex-project.ru


## About

Coded by Aleksey Melnikov at Apex Project bureau, Moscow

These scripts are avariable and easy to use thanks to pyRevit project by Ehsan Iran-Nejad

License: This package is licensed under GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.
