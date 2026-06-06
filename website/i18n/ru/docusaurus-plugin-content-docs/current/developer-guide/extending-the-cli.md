---
sidebar_position: 8
title: "Расширение CLI"
description: "Создай обёртки CLI, которые расширяют Hermes TUI пользовательскими виджетами, привязками клавиш и изменениями макета"
---

# Расширение CLI

Hermes предоставляет защищённые точки расширения в `HermesCLI`, чтобы обёртки CLI могли добавлять виджеты, привязки клавиш и настройки макета без переопределения 1000‑строчного метода `run()`. Это позволяет твоему расширению оставаться независимым от внутренних изменений.

## Точки расширения

Доступно пять точек расширения:

| Hook | Назначение | Переопределять, когда… |
|------|------------|------------------------|
| `_get_extra_tui_widgets()` | Вставка виджетов в макет | Нужно постоянный элемент UI (панель, строка статуса, мини‑плеер) |
| `_register_extra_tui_keybindings(kb, *, input_area)` | Добавление сочетаний клавиш | Нужны горячие клавиши (переключение панелей, управление транспортом, модальные сочетания) |
| `_build_tui_layout_children(**widgets)` | Полный контроль над порядком виджетов | Нужно переупорядочить или обернуть существующие виджеты (редко) |
| `process_command()` | Добавление пользовательских слеш‑команд | Нужно обработать `/mycommand` (существующая точка) |
| `_build_tui_style_dict()` | Пользовательские стили prompt_toolkit | Нужно задать свои цвета или стили (существующая точка) |

Первые три — новые защищённые хуки. Последние два уже существовали.

## Быстрый старт: обёртка CLI

```python
#!/usr/bin/env python3
"""my_cli.py — Example wrapper CLI that extends Hermes."""

from cli import HermesCLI
from prompt_toolkit.layout import FormattedTextControl, Window
from prompt_toolkit.filters import Condition


class MyCLI(HermesCLI):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._panel_visible = False

    def _get_extra_tui_widgets(self):
        """Add a toggleable info panel above the status bar."""
        cli_ref = self
        return [
            Window(
                FormattedTextControl(lambda: "📊 My custom panel content"),
                height=1,
                filter=Condition(lambda: cli_ref._panel_visible),
            ),
        ]

    def _register_extra_tui_keybindings(self, kb, *, input_area):
        """F2 toggles the custom panel."""
        cli_ref = self

        @kb.add("f2")
        def _toggle_panel(event):
            cli_ref._panel_visible = not cli_ref._panel_visible

    def process_command(self, cmd: str) -> bool:
        """Add a /panel slash command."""
        if cmd.strip().lower() == "/panel":
            self._panel_visible = not self._panel_visible
            state = "visible" if self._panel_visible else "hidden"
            print(f"Panel is now {state}")
            return True
        return super().process_command(cmd)


if __name__ == "__main__":
    cli = MyCLI()
    cli.run()
```

Запусти её:

```bash
cd ~/.hermes/hermes-agent
source .venv/bin/activate
python my_cli.py
```

## Справочник по хукам

### `_get_extra_tui_widgets()`

Возвращает список виджетов prompt_toolkit, которые будут вставлены в макет TUI. Виджеты отображаются **между разделителем и строкой статуса** — над областью ввода, но ниже основного вывода.

```python
def _get_extra_tui_widgets(self) -> list:
    return []  # default: no extra widgets
```

Каждый виджет должен быть контейнером prompt_toolkit (например, `Window`, `ConditionalContainer`, `HSplit`). Используй `ConditionalContainer` или `filter=Condition(...)`, чтобы сделать виджеты переключаемыми.

```python
from prompt_toolkit.layout import ConditionalContainer, Window, FormattedTextControl
from prompt_toolkit.filters import Condition

def _get_extra_tui_widgets(self):
    return [
        ConditionalContainer(
            Window(FormattedTextControl("Status: connected"), height=1),
            filter=Condition(lambda: self._show_status),
        ),
    ]
```

### `_register_extra_tui_keybindings(kb, *, input_area)`

Вызывается после того, как Hermes регистрирует свои привязки клавиш и до построения макета. Добавляй свои привязки в `kb`.

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    pass  # default: no extra keybindings
```

**Параметры**
- **`kb`** — экземпляр `KeyBindings` для приложения prompt_toolkit
- **`input_area`** — основной виджет `TextArea`, если нужно читать или изменять ввод пользователя

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    cli_ref = self

    @kb.add("f3")
    def _clear_input(event):
        input_area.text = ""

    @kb.add("f4")
    def _insert_template(event):
        input_area.text = "/search "
```

**Избегай конфликтов** со встроенными привязками: `Enter` (отправка), `Escape Enter` (новая строка), `Ctrl-C` (прерывание), `Ctrl-D` (выход), `Tab` (принятие автодополнения). Клавиши F2+ и комбинации Ctrl обычно безопасны.

### `_build_tui_layout_children(**widgets)`

Переопределяй только тогда, когда нужен полный контроль над порядком виджетов. Большинству расширений достаточно использовать `_get_extra_tui_widgets()`.

```python
def _build_tui_layout_children(self, *, sudo_widget, secret_widget,
    approval_widget, clarify_widget, model_picker_widget=None,
    spinner_widget=None, spacer, status_bar, input_rule_top,
    image_bar, input_area, input_rule_bot, voice_status_bar,
    completions_menu) -> list:
```

Реализация по умолчанию возвращает (виджеты, равные `None`, отфильтровываются):

```python
[
    Window(height=0),       # anchor
    sudo_widget,            # sudo password prompt (conditional)
    secret_widget,          # secret input prompt (conditional)
    approval_widget,        # dangerous command approval (conditional)
    clarify_widget,         # clarify question UI (conditional)
    model_picker_widget,    # model picker overlay (conditional)
    spinner_widget,         # thinking spinner (conditional)
    spacer,                 # fills remaining vertical space
    *self._get_extra_tui_widgets(),  # YOUR WIDGETS GO HERE
    status_bar,             # model/token/context status line
    input_rule_top,         # ─── border above input
    image_bar,              # attached images indicator
    input_area,             # user text input
    input_rule_bot,         # ─── border below input
    voice_status_bar,       # voice mode status (conditional)
    completions_menu,       # autocomplete dropdown
]
```

## Диаграмма макета

Макет по умолчанию сверху вниз:

1. **Область вывода** — прокручиваемая история диалога
2. **Разделитель**
3. **Дополнительные виджеты** — из `_get_extra_tui_widgets()`
4. **Строка статуса** — модель, % контекста, время выполнения
5. **Панель изображений** — количество прикреплённых изображений
6. **Область ввода** — запрос пользователя
7. **Статус голоса** — индикатор записи
8. **Меню автодополнений** — предложения автодополнения

## Советы

- **Инвалидировать отображение** после изменения состояния: вызови `self._invalidate()`, чтобы вызвать перерисовку prompt_toolkit.
- **Доступ к состоянию агента**: `self.agent`, `self.model`, `self.conversation_history` доступны.
- **Пользовательские стили**: переопредели `_build_tui_style_dict()` и добавь записи для своих классов стилей.
- **Слеш‑команды**: переопредели `process_command()`, обработай свои команды и вызови `super().process_command(cmd)` для остальных.
- **Не переопределяй `run()`**, если это не абсолютно необходимо — хуки расширения созданы именно для того, чтобы избежать такой привязки.