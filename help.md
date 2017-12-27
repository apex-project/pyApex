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

---

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

---

### Zoom Base Point

###### EN

Zoom in active view to Project base point. If it's hidden - enables "Reveal Hidden" mode.

> Shift+Click - find Shared Site point

###### RU

Находит базовую точку проекта на текущем виде. Если точка скрыта - включает режим показа скрытых объектов.

> Shift+Click - найти Точку съемки

---

## 2. Model

### Remove Level

__beta__

###### EN

Remove selected level safely - transfer all dependent elements to another level. First select levels you want to remove, then select level where you want to move orphan elements.

> No elements will be moved physically, only their Base level is being changed.

###### RU

Аккуратно удаляет выбранные уровни, перемещая все зависимые элементы, на другой уровень. Сначала выберите уровни, которые хотите удалить. Затем выберите уровень, к которому нужно привязать зависимые элементы.

> Элементы остаются на своих местах, просто меняется из базовый уровень.

---

### Objects on level

###### EN

List elements dependent on selected levels. To setup exceptions and limit run with Shift-click.

> Context: You can either activate a Plan View, select Plan Views in project browser or select Levels on a section. If nothing selected, you'll be able to choise levels from a list.

> How it works: Script tries to delete a level and looks for dependent elements.

###### RU

Выдает список элементов, зависимых от выбранных видов. Для настроек исключения и ограничения кол-ва элементов, которые выводятся в списке, запустите с зажатым Shift

> Контекст: Можно либо активировать План, либо выбрать Планы в Браузере проекта, либо выбрать уровни на разрезе или фасаде. Если ничего не выбрано, вам будет предложено выбрать уровнь из списка.

> Принцип работы: Скрипт пытается удалить уровнь, а затем определяет, какие элементы были затронуты

---

### Unjoin many

###### EN

Unjoins all selected geometry. (undo Join command)

Useful to get rid of warnings "Highlighted Elements are Joined but do not Intersect"

> Context: Some elements should be selected

###### RU

Разъединяет все выбранные элементы. (отменяет команду Соединить)

Полезно в случаях, когда нужно избавиться от предупреждения "Элементы соединены, но не пересекаются"

> Контекст: Должно быть выбрано несколько элементов

---

## 3. Detail

### Copy VG Filters

###### EN

Copying filter overrides from selected or active view to chosen view templates. If VG override for this filter already exists in a template it will be updated.

> Context: Select or activate a view

###### RU

Копирует настройки фильтров из настроек "Переопределения видимости/графики" для текущего вида в выбраныне шеблоны видов.
Если для фильтра уже заданы переопределения в целевом шаблоне, они будут обновлены.

> Контекст: Выбранный или активный вид

---

### Text Notes 2 CSV

###### EN

Export all textnotes content to csv.

> Context: select views or sheets where you want to search for textnotes

> If nothing selected it will search through all views in project. If sheets selected it will search both on sheet view and on views placed on the sheet.

###### RU

Экспорт содержимого всех "Текстов" в csv-файл.

> Контекст: выберите виды или листы, на которых необходимо найти тексты

> Если ничего не выбрано, поиск будет выполняться по всем видам в проекте. Если выбран Лист, поиск будет выполняться как на листе, так и на видах, размещенных на листе

---

## 4. Misc

### SheetsEnum 

###### EN

Sort selected objects, views or sheets by specified parameter, coordinate or along curve. 
Then write order number of each element as another parameter

> Context: at least 2 objects must be selected

###### RU

Сортирует выделенные объекты, виды или листы по определенному параметру, координате или вдоль линии.
Затем записывает порядковый номер каждого из объектов в другой параметр.

> Контекст: как минимум 2 объекта должны быть выделены

---

### White Materials

useful for render. Change all material appearance to white and back. Exceptions are WIP.

### Objects on Worksets

show list of objects which belongs to selected workset. Useful to check before deleting the workset.

### Worksets for links

create worksets for all types of links.

### Purge recursively

open each family and purge its content recursively

### Select duplicate tags

