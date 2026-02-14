# MarmosetLink

Универсальный мост для интеграции Autodesk Maya и Marmoset Toolbag.
Позволяет экспортировать FBX и автоматически запускать запекание (Bake) в один клик.

## Установка

### 1. Marmoset Toolbag 3 (Общая часть)
1.  В Marmoset Toolbag перейдите в меню `Edit -> Plugins -> Show User Plugin Folder`. Откроется папка со скриптами.
2.  Скопируйте файл `marmoset_scripts/mset_external_listener.py` в эту открывшуюся папку.
3.  В Marmoset Toolbag выберите `Edit -> Plugins -> Refresh` для обновления списка плагинов.
4.  Снова откройте `Edit -> Plugins` и найдите `mset_external_listener`. Нажмите на него, чтобы активировать (появится галочка/чекбокс).
    *   Теперь плагин работает и слушает команды из любого 3D-пакета.

### 2. Интеграции

#### Autodesk Maya
1.  Скопируйте папку `maya_mset_integration` в стандартную папку скриптов Maya (например, `C:\Users\user\Documents\maya\2025\scripts`).

### Быстрая установка кнопок (Shelf)
Для автоматического создания кнопок **HP**, **LP**, **Bake** на текущей полке:
1.  Найдите файл `maya_mset_integration/install_shelf.mel`.
2.  Перетащите его (Drag & Drop) из проводника прямо во вьюпорт Maya.
3.  На текущей полке появятся 3 кнопки.
    *   **ЛКМ** по кнопке: выполнение действия (Экспорт/Бейк).
    *   **ПКМ** по кнопке -> **Settings**: открытие окна настроек.

## Настройка

Для настройки путей экспорта и параметров (Unlock Normals, Freeze Normals, Triangulate) используйте графический интерфейс.

### Через Shelf (рекомендуется)
Если вы установили кнопки на полку, просто нажмите **ПКМ** по любой из кнопок (HP, LP, Bake) и выберите **Settings**.

### Через скрипт
Вы также можете запустить окно настроек кодом:
```python
import importlib
import maya_mset_integration.maya_mset_settings_gui as mset_gui
importlib.reload(mset_gui) 
mset_gui.main()
```

### Вручную (через JSON)
Настройки хранятся в файле `config.json`, который находится в той же папке, что и скрипты (`maya_mset_integration/config.json`).
Если запись в эту папку невозможна (нет прав), файл будет создан в домашней директории пользователя.
```json
{
    "hp_path": "C:/Path/To/Your/Project/HighPoly.fbx",
    "lp_path": "C:/Path/To/Your/Project/LowPoly.fbx",
    "unlock_normals": true,
    "freeze_normals": true,
    "triangulate": true
}
```

## Использование

### Шаг 1: Запустите слушатель в Marmoset
Скрипт `mset_external_listener.py` должен быть запущен и работать в фоновом режиме в Marmoset Toolbag.

### Шаг 2: Запуск команд из Maya

Вы можете запускать эти команды из Script Editor (вкладка Python) или добавить их на полку (Shelf).

**Экспорт High Poly + Bake:**
```python
import importlib
import maya_mset_integration.maya_mset_export_hp as hp_exp
importlib.reload(hp_exp) 
hp_exp.main()
```

**Экспорт Low Poly + Bake:**
*Выполняет оптимизацию меша (Triangulate, Unlock/Freeze Normals), экспорт и Bake.*
```python
import importlib
import maya_mset_integration.maya_mset_export_lp as lp_exp
importlib.reload(lp_exp)
lp_exp.main()
```

**Только Bake (без экспорта):**
*Только отправляет команду Rebake в Marmoset.*
```python
import importlib
import maya_mset_integration.maya_mset_bake as mset_bake
importlib.reload(mset_bake)
mset_bake.main()
```

## Устранение неполадок
*   Если Marmoset не реагирует, убедитесь, что `mset_external_listener.py` запущен.
*   Если скрипт в Maya зависает на этапе "Waiting for Marmoset report...", проверьте консоль Marmoset на наличие ошибок.

## Планируемые возможности (Roadmap)
*   **Запуск рендера**: Автоматический запуск рендера из Maya/ZBrush.
*   **Интеграция с ZBrush**: Экспорт SubTools и обновление сцены GoZ-style.
*   **Интеграция с Blender/Cinema 4D**: Поддержка других DCC пакетов.
