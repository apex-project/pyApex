---
layout: default
title: Features and help
permalink: /help
---

# Features and help

## 1. Selection

### Open Views

###### EN

To save time for rendering each view, this button opens all selected views in one click

> Context: Some views should be selected in project browser

###### RU

Открыть виды.

Чтобы сэкономить время, которое тратится на рендеринг при открытии вида, эта кнопка открывает несколько выделенных видов одним нажатием.

> Контекст: Должны быть выбраны несколько видов в браузере проекта


### Extract IDs from text

###### EN

Extracts all elements Ids from pasted text. Useful to select elements from Warnings - just copy text from HTML report:

Input:

```
Highlighted walls overlap. One of them may be ignored when Revit finds room boundaries. Use Cut Geometry to embed one wall within the other.	Walls : Basic Wall : EXT_M_CBL.250(I-INSpn.150-AIR.30-BRI.120)_550 : id 348661 
Walls : Basic Wall : EXT_M_CBL.250(I-INSpn.150-AIR.30-BRI.120)_550 : id 348663
```

Output:
```
348661,348663
```

Also works with one id per line inputs, e.g. with text copied from spreadsheets.

###### RU

Извлекает ID элементов из вставленного текста. Полезно для выбора элементов из отчетов о предупреждениях - просто скопируйте текст из HTML-отчета.

Также работает с текстом, в котором каждая строка - отдельный ID, например скопированным из таблицы.


### Zoom Base Point

---

## 2. Model

### Change Level

remove selected level and transfer all its object to another selected level

### Level Dependence

show elements dependen of selected levels

### Unjoin Selected

unjoin all selected geometry

### Unjoin Warnings

unjoin elements by pasted text from Warnings Reports

---

## 3. Detail

### Copy VG Filters

copying filter from one view template to others

### Text Notes 2 CSV

finds text notes on selected views and saves it's content to csv

---

## 4. Misc

### SheetsEnum 

enumerate selected sheets (WIP)

### White Materials

useful for render. Change all material appearance to white and back. Exceptions are WIP.

### Objects on Worksets

show list of objects which belongs to selected workset. Useful to check before deleting the workset.

### Worksets for links

create worksets for all types of links.

### Purge recursively

open each family and purge its content recursively

### Select duplicate tags

