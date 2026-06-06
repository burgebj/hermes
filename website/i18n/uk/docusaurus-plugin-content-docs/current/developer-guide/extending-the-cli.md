---
sidebar_position: 8
title: "Розширення CLI"
description: "Створюй обгорткові CLI, які розширюють Hermes TUI кастомними віджетами, прив’язками клавіш та змінами макету"
---

# Розширення CLI

Hermes надає захищені точки розширення в `HermesCLI`, щоб обгорткові CLI могли додавати віджети, прив’язки клавіш та налаштування макету без перевизначення 1000‑рядкового методу `run()`. Це дозволяє твоєму розширенню залишатися незалежним від внутрішніх змін.

## Точки розширення

Доступно п’ять точок розширення:

| Hook | Призначення | Перевизначити, коли… |
|------|-------------|----------------------|
| `_get_extra_tui_widgets()` | Вставити віджети в макет | Потрібен постійний елемент UI (панель, рядок стану, міні‑плеєр) |
| `_register_extra_tui_keybindings(kb, *, input_area)` | Додати клавіатурні скорочення | Потрібні гарячі клавіші (перемикання панелей, керування транспортом, модальні скорочення) |
| `_build_tui_layout_children(**widgets)` | Повний контроль над порядком віджетів | Потрібно переупорядкувати або обгорнути існуючі віджети (рідко) |
| `process_command()` | Додати власні slash‑команди | Потрібна обробка `/mycommand` (вбудована точка) |
| `_build_tui_style_dict()` | Користувацькі стилі prompt_toolkit | Потрібні власні кольори або оформлення (вбудована точка) |

Перші три — нові захищені точки. Останні два вже існували.

## Швидкий старт: обгортковий CLI

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

Запусти його:

```bash
cd ~/.hermes/hermes-agent
source .venv/bin/activate
python my_cli.py
```

## Довідка по точках

### `_get_extra_tui_widgets()`

Повертає список віджетів prompt_toolkit, які слід вставити в макет TUI. Віджети розташовуються **між розділювачем і рядком стану** — над областю вводу, але під основним виводом.

```python
def _get_extra_tui_widgets(self) -> list:
    return []  # default: no extra widgets
```

Кожен віджет має бути контейнером prompt_toolkit (наприклад, `Window`, `ConditionalContainer`, `HSplit`). Використовуй `ConditionalContainer` або `filter=Condition(...)`, щоб зробити віджети перемикаємими.

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

Викликається після того, як Hermes зареєструє власні прив’язки клавіш і до побудови макету. Додай свої прив’язки до `kb`.

```python
def _register_extra_tui_keybindings(self, kb, *, input_area):
    pass  # default: no extra keybindings
```

**Параметри**
- **`kb`** — екземпляр `KeyBindings` для застосунку prompt_toolkit
- **`input_area`** — головний віджет `TextArea`, якщо потрібно читати або змінювати ввід користувача

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

**Уникай конфліктів** з вбудованими прив’язками: `Enter` (відправка), `Escape Enter` (новий рядок), `Ctrl-C` (переривання), `Ctrl-D` (вихід), `Tab` (прийняття автопідказки). Клавіші функцій F2+ та комбінації Ctrl зазвичай безпечні.

### `_build_tui_layout_children(**widgets)`

Перевизначай це лише коли потрібен повний контроль над порядком віджетів. Більшість розширень мають користуватись `_get_extra_tui_widgets()`.

```python
def _build_tui_layout_children(self, *, sudo_widget, secret_widget,
    approval_widget, clarify_widget, model_picker_widget=None,
    spinner_widget=None, spacer, status_bar, input_rule_top,
    image_bar, input_area, input_rule_bot, voice_status_bar,
    completions_menu) -> list:
```

Типова реалізація повертає (будь‑які `None` віджети фільтруються):

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

## Діаграма макету

Типовий макет зверху вниз:

1. **Область виводу** — прокручувана історія розмов
2. **Розділювач**
3. **Додаткові віджети** — з `_get_extra_tui_widgets()`
4. **Рядок стану** — модель, % контексту, час виконання
5. **Рядок зображень** — кількість прикріплених зображень
6. **Область вводу** — підказка користувача
7. **Статус голосу** — індикатор запису
8. **Меню завершень** — підказки автодоповнення

## Поради

- **Скасуй відображення** після змін стану: виклич `self._invalidate()`, щоб ініціювати перерисовку prompt_toolkit.
- **Доступ до стану агента**: `self.agent`, `self.model`, `self.conversation_history` доступні.
- **Користувацькі стилі**: перевизнач `_build_tui_style_dict()` і додай записи для власних класів стилю.
- **Slash‑команди**: перевизнач `process_command()`, оброби свої команди та виклич `super().process_command(cmd)` для всього іншого.
- **Не перевизначай `run()`**, якщо це не абсолютно необхідно — точки розширення існують саме для уникнення такого зв’язування.