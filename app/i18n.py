from __future__ import annotations

LANGUAGES = {"en": "English", "uk": "Українська", "ru": "Русский"}
_language = "en"

_TEXT = {
    "en": {
        "settings": "Settings", "game_folder": "Game folder", "developer_mode": "Developer Mode", "developer_hint": "Show technical IDs and asset sources", "language": "Language", "theme": "Theme", "mouse_remapping": "Mouse buttons", "mouse_remapping_hint": "Enable M3, M4 and M5 bindings while Zero Hour is active", "mouse_proxy": "{button} internal key", "mouse_proxy_duplicate": "Each mouse button needs a different internal key.", "mouse_extra_buttons_hint": "Internal keys are written to generals.csf; the less commonly used 7, 8 and 9 are defaults. The editor must remain running. If Zero Hour runs as administrator, run the editor as administrator too. Windows exposes only M3-M5 as standard mouse buttons; configure additional vendor buttons as keyboard keys in your mouse software.",
        "select_game": "Select Command & Conquer Generals - Zero Hour folder", "game_not_found": "Game not found", "game_not_found_text": "Select a folder containing INIZH.big and TexturesZH.big.",
        "search": "Search Humvee, Raptor, Tunnel…", "indexing": "Indexing Zero Hour resources…", "select_command": "Select a command icon to change its hotkey.", "unsaved": "Unsaved changes: {count}",
        "apply": "Apply", "undo": "Undo", "redo": "Redo", "clear_all_bindings": "Clear all bindings", "save_profile": "Save Profile…", "manage_profiles": "Manage Profiles…", "file": "File", "profiles": "Profiles",
        "clear_all_bindings_text": "Clear all command-bar hotkeys for every faction and general?\n\nThe changes remain unsaved until you click Apply. Global system shortcuts are not affected.", "bindings_cleared": "Cleared bindings: {count}",
        "restore_latest": "Restore latest backup", "restore_original": "Restore original", "open_backup": "Open backup folder", "current_capture": "Current: {key}   •   Press new key…   •   Esc cancels",
        "none": "None", "shared": "Shared label: changing this key affects {count} commands — {names}", "cannot_assign": "Cannot assign key", "applied": "Applied", "applied_text": "Hotkeys applied safely.\nBackup: {backup}",
        "apply_failed": "Apply failed", "apply_failed_text": "The original file was not replaced.\n\n{error}", "restore": "Restore", "no_backup": "No backup is available.", "restored": "Restored",
        "latest_restored": "Latest backup restored. Restart the editor to reload it.", "restore_failed": "Restore failed", "already_original": "The game is already using the original CSF from EnglishZH.big.",
        "original_restored": "Loose override removed. The game will use the original CSF from EnglishZH.big.", "profile_name": "Profile name", "profile_saved": "Profile saved: {name}", "profile": "Profile",
        "load_profile": "Load Profile", "json_profiles": "JSON profiles (*.json)", "indexed": "Indexed {count} visual commands • {warnings} warnings", "index_failed": "Indexing failed",
        "imported_game_profile": "Imported game settings", "existing_profile_imported": "Existing game hotkeys saved as a profile",
        "loose_csf_invalid": "The editor could not read your hotkey configuration file:\n{path}\n\nThe file is damaged or was created by an incompatible CSF editor. Zero Hour may still accept it, but this editor cannot safely identify all of its records.\n\nRecommendations:\n• Do not delete it; make a copy first.\n• Try opening and resaving the copy with a CSF editor.\n• Restore a known-good backup, or rename generals.csf to make the game use the original from EnglishZH.big.\n\nTechnical reason: {error}",
        "archive_csf_invalid": "The original string table inside EnglishZH.big could not be read:\n{path}\n\nThe game archive may be damaged or belong to an unsupported mod/version. Verify the game files in Steam or EA App, or restore the matching EnglishZH.big.\n\nTechnical reason: {error}",
        "conflict": "Hotkey conflict", "conflict_text": "{key} is already assigned to {names} in {producer}.", "replace": "Replace", "choose_another": "Choose another", "cancel": "Cancel",
        "conflict_replace": "{key} is already assigned to:\n\n{locations}\n\nReplace it and clear the old binding?",
        "duplicate": "Duplicate", "rename": "Rename", "delete": "Delete", "import": "Import", "export": "Export", "apply_profile": "Apply selected profile", "game_default": "Game Default", "new_name": "New name",
        "duplicate_profile": "Duplicate Profile", "rename_profile": "Rename Profile", "delete_profile": "Delete Profile", "delete_profile_q": "Delete {name}?", "import_profile": "Import Profile", "export_profile": "Export Profile",
        "general.vanilla": "Vanilla", "general.air_force": "Air Force", "general.laser": "Laser", "general.superweapon": "Superweapon", "general.tank": "Tank", "general.infantry": "Infantry",
        "general.nuclear": "Nuclear", "general.toxin": "Toxin", "general.stealth": "Stealth", "general.demolition": "Demolition", "tooltip.produced": "Produced at", "tooltip.hotkey": "Hotkey",
        "global_hotkeys": "Global Hotkeys…", "all": "All", "universal": "Universal commands", "action": "Action", "key": "Key", "category": "Category",
        "select_global": "Select a global command to see what it does.", "assign": "Assign", "remove": "Remove", "global_conflict": "Global hotkey conflict",
        "global_conflict_text": "{key} is already used by: {names}.\n\nReplace it and clear the old binding?", "unsupported_key": "Unsupported key",
        "unsupported_key_text": "Command-bar hotkeys support one A-Z or 0-9 key, or M3/M4/M5, without modifiers.", "global_applied": "Global hotkeys applied safely. Restart the game to load them.",
        "bindings_for_key": "Bindings on {key}", "remove_named_binding": "Remove: {name} — {location}", "global_binding_location": "Global ({shortcut})",
        "no_bindings_for_key": "This key has no bindings", "clear_key_bindings": "Clear everything from {key}", "clear_key_bindings_text": "Remove every command and global shortcut that uses {key}?\n\nThe changes remain unsaved until you click Apply.",
        "general_powers": "General Powers",
    },
    "uk": {
        "settings": "Налаштування", "game_folder": "Папка гри", "developer_mode": "Режим розробника", "developer_hint": "Показувати технічні ID та джерела ресурсів", "language": "Мова", "theme": "Тема", "mouse_remapping": "Кнопки миші", "mouse_remapping_hint": "Увімкнути бінди M3, M4 і M5, коли активне вікно Zero Hour", "mouse_proxy": "Внутрішня клавіша {button}", "mouse_proxy_duplicate": "Для кожної кнопки миші потрібна окрема внутрішня клавіша.", "mouse_extra_buttons_hint": "Внутрішні клавіші записуються в generals.csf; за замовчуванням вибрано менш уживані 7, 8 і 9. Редактор має залишатися запущеним. Якщо Zero Hour запущено від адміністратора, редактор теж слід запустити від адміністратора. Windows стандартно передає лише M3-M5; додаткові кнопки виробника призначте на клавіші у програмі своєї миші.",
        "select_game": "Виберіть папку Command & Conquer Generals - Zero Hour", "game_not_found": "Гру не знайдено", "game_not_found_text": "Виберіть папку, що містить INIZH.big і TexturesZH.big.",
        "search": "Пошук: Humvee, Raptor, Tunnel…", "indexing": "Індексація ресурсів Zero Hour…", "select_command": "Виберіть іконку команди, щоб змінити хоткей.", "unsaved": "Незбережені зміни: {count}",
        "apply": "Застосувати", "undo": "Скасувати", "redo": "Повторити", "clear_all_bindings": "Очистити всі бінди", "save_profile": "Зберегти профіль…", "manage_profiles": "Керування профілями…", "file": "Файл", "profiles": "Профілі",
        "clear_all_bindings_text": "Очистити всі хоткеї command bar для всіх фракцій і генералів?\n\nЗміни залишаться незбереженими, доки ви не натиснете «Застосувати». Глобальні системні комбінації не змінюються.", "bindings_cleared": "Очищено біндів: {count}",
        "restore_latest": "Відновити останню резервну копію", "restore_original": "Відновити оригінал", "open_backup": "Відкрити папку резервних копій", "current_capture": "Поточна: {key}   •   Натисніть нову клавішу…   •   Esc — скасувати",
        "none": "Немає", "shared": "Спільна мітка: зміна клавіші вплине на {count} команд — {names}", "cannot_assign": "Не вдалося призначити клавішу", "applied": "Застосовано", "applied_text": "Хоткеї безпечно застосовано.\nРезервна копія: {backup}",
        "apply_failed": "Помилка застосування", "apply_failed_text": "Оригінальний файл не було замінено.\n\n{error}", "restore": "Відновлення", "no_backup": "Резервних копій немає.", "restored": "Відновлено",
        "latest_restored": "Останню резервну копію відновлено. Перезапустіть редактор.", "restore_failed": "Помилка відновлення", "already_original": "Гра вже використовує оригінальний CSF з EnglishZH.big.",
        "original_restored": "Окремий override видалено. Гра використовуватиме оригінальний CSF з EnglishZH.big.", "profile_name": "Назва профілю", "profile_saved": "Профіль збережено: {name}", "profile": "Профіль",
        "load_profile": "Завантажити профіль", "json_profiles": "Профілі JSON (*.json)", "indexed": "Проіндексовано команд: {count} • попереджень: {warnings}", "index_failed": "Помилка індексації",
        "imported_game_profile": "Імпортовані налаштування гри", "existing_profile_imported": "Наявні хоткеї гри збережено як окремий профіль",
        "loose_csf_invalid": "Редактор не зміг прочитати ваш файл налаштувань хоткеїв:\n{path}\n\nФайл пошкоджений або створений несумісним CSF-редактором. Zero Hour іноді продовжує працювати з такими файлами, але цей редактор не може безпечно визначити всі записи.\n\nРекомендації:\n• Не видаляйте файл — спочатку створіть його копію.\n• Спробуйте відкрити й повторно зберегти копію в CSF-редакторі.\n• Відновіть справну резервну копію або перейменуйте generals.csf, щоб гра використала оригінал з EnglishZH.big.\n\nТехнічна причина: {error}",
        "archive_csf_invalid": "Не вдалося прочитати оригінальну таблицю текстів усередині EnglishZH.big:\n{path}\n\nАрхів гри може бути пошкоджений або належати непідтримуваному моду чи версії. Перевірте файли гри у Steam або EA App чи відновіть відповідний EnglishZH.big.\n\nТехнічна причина: {error}",
        "conflict": "Конфлікт хоткеїв", "conflict_text": "Клавішу {key} вже призначено для {names} у {producer}.", "replace": "Замінити", "choose_another": "Вибрати іншу", "cancel": "Скасувати",
        "conflict_replace": "Клавішу {key} вже призначено для:\n\n{locations}\n\nЗамінити її та очистити старе призначення?",
        "duplicate": "Дублювати", "rename": "Перейменувати", "delete": "Видалити", "import": "Імпорт", "export": "Експорт", "apply_profile": "Застосувати вибраний профіль", "game_default": "Початкові налаштування гри", "new_name": "Нова назва",
        "duplicate_profile": "Дублювати профіль", "rename_profile": "Перейменувати профіль", "delete_profile": "Видалити профіль", "delete_profile_q": "Видалити {name}?", "import_profile": "Імпортувати профіль", "export_profile": "Експортувати профіль",
        "general.vanilla": "Стандартна", "general.air_force": "Авіаційний генерал", "general.laser": "Лазерний генерал", "general.superweapon": "Генерал суперзброї", "general.tank": "Танковий генерал", "general.infantry": "Піхотний генерал",
        "general.nuclear": "Ядерний генерал", "general.toxin": "Токсичний генерал", "general.stealth": "Генерал маскування", "general.demolition": "Генерал-підривник", "tooltip.produced": "Виробляється у", "tooltip.hotkey": "Хоткей",
        "global_hotkeys": "Глобальні хоткеї…", "all": "Усі", "universal": "Універсальні команди", "action": "Дія", "key": "Клавіша", "category": "Категорія",
        "select_global": "Виберіть глобальну команду, щоб побачити її призначення.", "assign": "Призначити", "remove": "Прибрати", "global_conflict": "Конфлікт глобальних хоткеїв",
        "global_conflict_text": "Клавішу {key} вже використовує: {names}.\n\nЗамінити її та очистити старе призначення?", "unsupported_key": "Непідтримувана клавіша",
        "unsupported_key_text": "Хоткеї command bar підтримують одну клавішу A-Z, 0-9 або M3/M4/M5 без модифікаторів.", "global_applied": "Глобальні хоткеї безпечно застосовано. Перезапустіть гру.",
        "bindings_for_key": "Бінди на клавіші {key}", "remove_named_binding": "Прибрати: {name} — {location}", "global_binding_location": "Глобальний ({shortcut})",
        "no_bindings_for_key": "На цій клавіші немає біндів", "clear_key_bindings": "Очистити все з клавіші {key}", "clear_key_bindings_text": "Прибрати всі команди та глобальні комбінації, що використовують {key}?\n\nЗміни залишаться незбереженими, доки ви не натиснете «Застосувати».",
        "general_powers": "Генеральські здібності",
    },
    "ru": {
        "settings": "Настройки", "game_folder": "Папка игры", "developer_mode": "Режим разработчика", "developer_hint": "Показывать технические ID и источники ресурсов", "language": "Язык", "theme": "Тема", "mouse_remapping": "Кнопки мыши", "mouse_remapping_hint": "Включить бинды M3, M4 и M5, когда активно окно Zero Hour", "mouse_proxy": "Внутренняя клавиша {button}", "mouse_proxy_duplicate": "Для каждой кнопки мыши нужна отдельная внутренняя клавиша.", "mouse_extra_buttons_hint": "Внутренние клавиши записываются в generals.csf; по умолчанию выбраны менее используемые 7, 8 и 9. Редактор должен оставаться запущенным. Если Zero Hour запущена от администратора, редактор тоже следует запустить от администратора. Windows стандартно передаёт только M3-M5; дополнительные кнопки производителя назначьте на клавиши в программе своей мыши.",
        "select_game": "Выберите папку Command & Conquer Generals - Zero Hour", "game_not_found": "Игра не найдена", "game_not_found_text": "Выберите папку, содержащую INIZH.big и TexturesZH.big.",
        "search": "Поиск: Humvee, Raptor, Tunnel…", "indexing": "Индексация ресурсов Zero Hour…", "select_command": "Выберите иконку команды, чтобы изменить горячую клавишу.", "unsaved": "Несохранённые изменения: {count}",
        "apply": "Применить", "undo": "Отменить", "redo": "Повторить", "clear_all_bindings": "Очистить все бинды", "save_profile": "Сохранить профиль…", "manage_profiles": "Управление профилями…", "file": "Файл", "profiles": "Профили",
        "clear_all_bindings_text": "Очистить все горячие клавиши command bar для всех фракций и генералов?\n\nИзменения останутся несохранёнными, пока вы не нажмёте «Применить». Глобальные системные сочетания не изменяются.", "bindings_cleared": "Очищено биндов: {count}",
        "restore_latest": "Восстановить последнюю резервную копию", "restore_original": "Восстановить оригинал", "open_backup": "Открыть папку резервных копий", "current_capture": "Текущая: {key}   •   Нажмите новую клавишу…   •   Esc — отмена",
        "none": "Нет", "shared": "Общая метка: смена клавиши повлияет на {count} команд — {names}", "cannot_assign": "Не удалось назначить клавишу", "applied": "Применено", "applied_text": "Горячие клавиши безопасно применены.\nРезервная копия: {backup}",
        "apply_failed": "Ошибка применения", "apply_failed_text": "Оригинальный файл не был заменён.\n\n{error}", "restore": "Восстановление", "no_backup": "Резервных копий нет.", "restored": "Восстановлено",
        "latest_restored": "Последняя резервная копия восстановлена. Перезапустите редактор.", "restore_failed": "Ошибка восстановления", "already_original": "Игра уже использует оригинальный CSF из EnglishZH.big.",
        "original_restored": "Отдельный override удалён. Игра будет использовать оригинальный CSF из EnglishZH.big.", "profile_name": "Название профиля", "profile_saved": "Профиль сохранён: {name}", "profile": "Профиль",
        "load_profile": "Загрузить профиль", "json_profiles": "Профили JSON (*.json)", "indexed": "Проиндексировано команд: {count} • предупреждений: {warnings}", "index_failed": "Ошибка индексации",
        "imported_game_profile": "Импортированные настройки игры", "existing_profile_imported": "Существующие горячие клавиши игры сохранены как отдельный профиль",
        "loose_csf_invalid": "Редактор не смог прочитать ваш файл настроек горячих клавиш:\n{path}\n\nФайл повреждён или создан несовместимым CSF-редактором. Zero Hour иногда продолжает работать с такими файлами, но этот редактор не может безопасно определить все записи.\n\nРекомендации:\n• Не удаляйте файл — сначала создайте его копию.\n• Попробуйте открыть и повторно сохранить копию в CSF-редакторе.\n• Восстановите исправную резервную копию или переименуйте generals.csf, чтобы игра использовала оригинал из EnglishZH.big.\n\nТехническая причина: {error}",
        "archive_csf_invalid": "Не удалось прочитать исходную таблицу текстов внутри EnglishZH.big:\n{path}\n\nАрхив игры может быть повреждён или относиться к неподдерживаемому моду либо версии. Проверьте файлы игры в Steam или EA App или восстановите соответствующий EnglishZH.big.\n\nТехническая причина: {error}",
        "conflict": "Конфликт горячих клавиш", "conflict_text": "Клавиша {key} уже назначена для {names} в {producer}.", "replace": "Заменить", "choose_another": "Выбрать другую", "cancel": "Отмена",
        "conflict_replace": "Клавиша {key} уже назначена для:\n\n{locations}\n\nЗаменить её и очистить старое назначение?",
        "duplicate": "Дублировать", "rename": "Переименовать", "delete": "Удалить", "import": "Импорт", "export": "Экспорт", "apply_profile": "Применить выбранный профиль", "game_default": "Исходные настройки игры", "new_name": "Новое название",
        "duplicate_profile": "Дублировать профиль", "rename_profile": "Переименовать профиль", "delete_profile": "Удалить профиль", "delete_profile_q": "Удалить {name}?", "import_profile": "Импортировать профиль", "export_profile": "Экспортировать профиль",
        "general.vanilla": "Стандартная", "general.air_force": "Авиационный генерал", "general.laser": "Лазерный генерал", "general.superweapon": "Генерал супероружия", "general.tank": "Танковый генерал", "general.infantry": "Пехотный генерал",
        "general.nuclear": "Ядерный генерал", "general.toxin": "Токсиновый генерал", "general.stealth": "Генерал маскировки", "general.demolition": "Генерал-подрывник", "tooltip.produced": "Производится в", "tooltip.hotkey": "Горячая клавиша",
        "global_hotkeys": "Глобальные клавиши…", "all": "Все", "universal": "Универсальные команды", "action": "Действие", "key": "Клавиша", "category": "Категория",
        "select_global": "Выберите глобальную команду, чтобы увидеть её назначение.", "assign": "Назначить", "remove": "Убрать", "global_conflict": "Конфликт глобальных клавиш",
        "global_conflict_text": "Клавишу {key} уже использует: {names}.\n\nЗаменить её и очистить старое назначение?", "unsupported_key": "Неподдерживаемая клавиша",
        "unsupported_key_text": "Клавиши command bar поддерживают одну клавишу A-Z, 0-9 или M3/M4/M5 без модификаторов.", "global_applied": "Глобальные клавиши безопасно применены. Перезапустите игру.",
        "bindings_for_key": "Бинды на клавише {key}", "remove_named_binding": "Убрать: {name} — {location}", "global_binding_location": "Глобальная ({shortcut})",
        "no_bindings_for_key": "На этой клавише нет биндов", "clear_key_bindings": "Очистить всё с клавиши {key}", "clear_key_bindings_text": "Убрать все команды и глобальные сочетания, использующие {key}?\n\nИзменения останутся несохранёнными, пока вы не нажмёте «Применить».",
        "general_powers": "Генеральские способности",
    },
}

def set_language(code: str) -> None:
    global _language
    _language = code if code in LANGUAGES else "en"

def current_language() -> str:
    return _language

def tr(message_id: str, **values) -> str:
    template = _TEXT.get(_language, _TEXT["en"]).get(message_id, _TEXT["en"].get(message_id, message_id))
    return template.format(**values)
