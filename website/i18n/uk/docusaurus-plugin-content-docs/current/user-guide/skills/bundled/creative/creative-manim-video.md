---
title: "Manim Video — анімації Manim CE: відео з математики/алгоритмів 3Blue1Brown"
sidebar_label: "Manim Video"
description: "Анімації Manim CE: відео з математики/алгоритмів від 3Blue1Brown"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Manim відео

Анімації Manim CE: відео з математики та алгоритмів від 3Blue1Brown.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/creative/manim-video` |
| Версія | `1.0.0` |
| Платформи | linux, macos, windows |
:::info
Нижче наведено повне визначення skill, яке Hermes завантажує, коли цей skill активовано. Це інструкції, які бачить агент під час роботи skill.
:::

# Конвеєр виробництва відео Manim
## Коли використовувати

Використовуй, коли користувачі запитують: анімовані пояснення, математичні анімації, візуалізації концепцій, покрокові розбори алгоритмів, технічні пояснювальні матеріали, відео у стилі 3Blue1Brown або будь‑яку програмну анімацію з геометричним/математичним вмістом. Створює відео‑пояснювальні у стилі 3Blue1Brown, візуалізації алгоритмів, виведення рівнянь, діаграми архітектури та історії даних за допомогою Manim Community Edition.
## Creative Standard

Це освітнє кіно. Кожен кадр навчає. Кожна анімація розкриває структуру.

**Before writing a single line of code**, сформулюй сюжетну дугу. Яке неправильне уявлення це виправляє? Який «aha‑момент»? Яка візуальна історія проводить глядача від плутанини до розуміння? Запит користувача — лише відправна точка, інтерпретуй його з педагогічною амбіцією.

**Geometry before algebra.** Спочатку покажи форму, потім рівняння. Візуальна пам’ять кодується швидше, ніж символічна. Коли глядач бачить геометричний шаблон перед формулою, рівняння здається заслуженим.

**First-render excellence is non‑negotiable.** Вихід має бути візуально чітким і естетично узгодженим без додаткових раундів правок. Якщо щось виглядає захаращеним, погано синхронізованим або схожим на «AI‑generated slides», це помилка.

**Opacity layering directs attention.** Ніколи не показуй усе на повній яскравості. Основні елементи — 1.0, контекстуальні — 0.4, структурні (вісі, сітки) — 0.15. Мозок обробляє візуальну виразність у шарах.

**Breathing room.** Кожна анімація потребує `self.wait()` після неї. Глядач потребує часу, щоб усвідомити те, що лише з’явилося. Не поспішай від однієї анімації до іншої. Пауза у 2 секунди після ключового розкриття ніколи не є зайвою.

**Cohesive visual language.** Усі сцени мають спільну колірну палітру, послідовні розміри типографіки, однакову швидкість анімації. Технічно правильне відео, у якому кожна сцена використовує випадкові різні кольори, — це естетичний провал.
## Передумови

Запусти `scripts/setup.sh`, щоб перевірити всі залежності. Потрібно: Python 3.10+, Manim Community Edition v0.20+ (`pip install manim`), LaTeX (`texlive-full` на Linux, `mactex` на macOS) та ffmpeg. Документація протестована з Manim CE v0.20.1.
## Режими

| Режим | Вхідні дані | Вихід | Посилання |
|------|------------|------|-----------|
| **Concept explainer** | Тема/концепція | Анімоване пояснення з геометричною інтуїцією | `references/scene-planning.md` |
| **Equation derivation** | Математичні вирази | Покрокове анімоване доведення | `references/equations.md` |
| **Algorithm visualization** | Опис алгоритму | Покрокове виконання з використанням структур даних | `references/graphs-and-data.md` |
| **Data story** | Дані/метрики | Анімовані діаграми, порівняння, лічильники | `references/graphs-and-data.md` |
| **Architecture diagram** | Опис системи | Компоненти, що формуються та з’єднуються | `references/mobjects.md` |
| **Paper explainer** | Наукова стаття | Ключові результати та методи у вигляді анімації | `references/scene-planning.md` |
| **3D visualization** | 3D‑концепція | Обертання поверхонь, параметричні криві, просторову геометрію | `references/camera-and-3d.md` |
## Stack

Один скрипт Python на проєкт. Без браузера, без Node.js, без GPU.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Manim Community Edition | Рендеринг сцен, анімаційний движок |
| Math | LaTeX (texlive/MiKTeX) | Візуалізація рівнянь через `MathTex` |
| Video I/O | ffmpeg | Зшивання сцен, конвертація форматів, мультиплексування аудіо |
| TTS | ElevenLabs / Qwen3-TTS (optional) | Озвучення нарації |
## Конвеєр

```
PLAN --> CODE --> RENDER --> STITCH --> AUDIO (optional) --> REVIEW
```

1. **PLAN** — створити `plan.md` з описом сюжетної арки, списком сцен, візуальними елементами, палітрою кольорів, сценарієм озвучення
2. **CODE** — написати `script.py`, де для кожної сцени окремий клас, який можна рендерити самостійно
3. **RENDER** — `manim -ql script.py Scene1 Scene2 …` для чернетки, `-qh` — для фінального рендеру
4. **STITCH** — об’єднати кліпи сцен за допомогою ffmpeg concat у файл `final.mp4`
5. **AUDIO** (необов’язково) — додати озвучення та/або фонову музику за допомогою ffmpeg. Див. `references/rendering.md`
6. **REVIEW** — згенерувати попередні кадри, перевірити їх відповідність плану та внести корективи
## Структура проєкту

```
project-name/
  plan.md                # Narrative arc, scene breakdown
  script.py              # All scenes in one file
  concat.txt             # ffmpeg scene list
  final.mp4              # Stitched output
  media/                 # Auto-generated by Manim
    videos/script/480p15/
```
## Творчий напрямок

### Кольорові палітри

| Палітра | Фон | Основний | Другорядний | Акцент | Випадок використання |
|---------|-----------|---------|-----------|--------|----------------------|
| **Classic 3B1B** | `#1C1C1C` | `#58C4DD` (BLUE) | `#83C167` (GREEN) | `#FFFF00` (YELLOW) | Загальна математика/CS |
| **Warm academic** | `#2D2B55` | `#FF6B6B` | `#FFD93D` | `#6BCB77` | Доступний |
| **Neon tech** | `#0A0A0A` | `#00F5FF` | `#FF00FF` | `#39FF14` | Системи, архітектура |
| **Monochrome** | `#1A1A2E` | `#EAEAEA` | `#888888` | `#FFFFFF` | Мінімалістичний |

### Швидкість анімації

| Контекст | run_time | self.wait() після |
|---------|----------|-------------------|
| Поява заголовка/вступу | 1.5s | 1.0s |
| Відкриття ключового рівняння | 2.0s | 2.0s |
| Перетворення/морфінг | 1.5s | 1.5s |
| Підтримуюча підпис | 0.8s | 0.5s |
| Очищення FadeOut | 0.5s | 0.3s |
| Відкриття «моменту Ага» | 2.5s | 3.0s |

### Шкала типографіки

| Роль | Розмір шрифту | Використання |
|------|---------------|---------------|
| Заголовок | 48 | Заголовки сцен, відкритий текст |
| Заголовок розділу | 36 | Заголовки розділів у сцені |
| Текст | 30 | Пояснювальний текст |
| Мітка | 24 | Анотації, підписи осей |
| Підпис | 20 | Субтитри, дрібний шрифт |

### Шрифти

**Використовуй моноширинні шрифти для всього тексту.** Рендерер Pango у Manim створює пошкоджений кернінґ при пропорційних шрифтах будь‑якого розміру. Дивись `references/visual-design.md` для повних рекомендацій.

```python
MONO = "Menlo"  # define once at top of file

Text("Fourier Series", font_size=48, font=MONO, weight=BOLD)  # titles
Text("n=1: sin(x)", font_size=20, font=MONO)                  # labels
MathTex(r"\nabla L")                                            # math (uses LaTeX)
```

Мінімум `font_size=18` для читабельності.

### Варіація між сценами

Ніколи не використовуйте однакову конфігурацію для всіх сцен. Для кожної сцени:
- **Інший домінуючий колір** з палітри
- **Інший макет** — не завжди центрируй все
- **Інший вхід анімації** — чергуй Write, FadeIn, GrowFromCenter, Create
- **Інша візуальна вага** — деякі сцени щільні, інші — розріджені
## Workflow

### Крок 1: План (plan.md)

Перед будь‑яким кодом напиши `plan.md`. Дивись `references/scene-planning.md` для комплексного шаблону.

### Крок 2: Код (script.py)

По одному класу на сцену. Кожна сцена рендериться незалежно.

```python
from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
MONO = "Menlo"

class Scene1_Introduction(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("Why Does This Work?", font_size=48, color=PRIMARY, weight=BOLD, font=MONO)
        self.add_subcaption("Why does this work?", duration=2)
        self.play(Write(title), run_time=1.5)
        self.wait(1.0)
        self.play(FadeOut(title), run_time=0.5)
```

Ключові шаблони:
- **Subtitles** на кожній анімації: `self.add_subcaption("text", duration=N)` або `subcaption="text"` у `self.play()`
- **Shared color constants** у верхній частині файлу для крос‑сценічної узгодженості
- **`self.camera.background_color`** встановлюється в кожній сцені
- **Clean exits** — FadeOut всіх mobjects в кінці сцени: `self.play(FadeOut(Group(*self.mobjects)))`

### Крок 3: Рендер

```bash
manim -ql script.py Scene1_Introduction Scene2_CoreConcept  # draft
manim -qh script.py Scene1_Introduction Scene2_CoreConcept  # production
```

### Крок 4: Зшивання

```bash
cat > concat.txt << 'EOF'
file 'media/videos/script/480p15/Scene1_Introduction.mp4'
file 'media/videos/script/480p15/Scene2_CoreConcept.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4
```

### Крок 5: Огляд

```bash
manim -ql --format=png -s script.py Scene2_CoreConcept  # preview still
```
## Критичні нотатки щодо реалізації

### Raw Strings for LaTeX
```python
# WRONG: MathTex("\frac{1}{2}")
# RIGHT:
MathTex(r"\frac{1}{2}")
```

### buff >= 0.5 для Edge Text
```python
label.to_edge(DOWN, buff=0.5)  # never < 0.5
```

### FadeOut перед заміною тексту
```python
self.play(ReplacementTransform(note1, note2))  # not Write(note2) on top
```

### Ніколи не анімувати не додані Mobjects
```python
self.play(Create(circle))  # must add first
self.play(circle.animate.set_color(RED))  # then animate
```
## Цілі продуктивності

| Якість | Роздільна здатність | FPS | Швидкість |
|--------|---------------------|-----|-----------|
| `-ql` (чернетка) | 854×480 | 15 | 5‑15 s/scene |
| `-qm` (середній) | 1280×720 | 30 | 15‑60 s/scene |
| `-qh` (виробничий) | 1920×1080 | 60 | 30‑120 s/scene |

Завжди працюй у режимі `-ql`. Використовуй `-qh` лише для фінального рендеру.
## Посилання

| Файл | Вміст |
|------|----------|
| `references/animations.md` | Основні анімації, функції швидкості, композиція, синтаксис `.animate`, шаблони таймінгу |
| `references/mobjects.md` | Текст, форми, `VGroup`/`Group`, позиціонування, стилізація, користувацькі mobjects |
| `references/visual-design.md` | 12 принципів дизайну, прозорість шарів, шаблони макетів, колірні палітри |
| `references/equations.md` | LaTeX у Manim, `TransformMatchingTex`, шаблони виведення |
| `references/graphs-and-data.md` | Вісі, побудова графіків, `BarChart`, анімовані дані, візуалізація алгоритмів |
| `references/camera-and-3d.md` | `MovingCameraScene`, `ThreeDScene`, 3D‑поверхні, керування камерою |
| `references/scene-planning.md` | Наративні арки, шаблони макетів, переходи між сценами, шаблон планування |
| `references/rendering.md` | Довідка CLI, пресети якості, `ffmpeg`, воркфлоу озвучування, експорт GIF |
| `references/troubleshooting.md` | Помилки LaTeX, помилки анімації, типові помилки, налагодження |
| `references/animation-design-thinking.md` | Коли анімувати, а коли показувати статично, декомпозиція, темп, синхронізація озвучення |
| `references/updaters-and-trackers.md` | `ValueTracker`, `add_updater`, `always_redraw`, оновлювачі, що залежать від часу, шаблони |
| `references/paper-explainer.md` | Перетворення наукових статей в анімації — процес, шаблони, доменні шаблони |
| `references/decorations.md` | `SurroundingRectangle`, `Brace`, стрілки, `DashedLine`, `Angle`, життєвий цикл анотацій |
| `references/production-quality.md` | pre‑code, pre‑render, контрольні списки після рендеру, просторове розташування, колір, темп |
## Creative Divergence (використовуй лише коли користувач запитує експериментальний/креативний/унікальний результат)

Якщо користувач просить креативний, експериментальний або нестандартний підхід до пояснення, обери стратегію і обґрунтуй її **до** створення анімації.

- **SCAMPER** — коли користувач хоче свіжий погляд на стандартне пояснення
- **Assumption Reversal** — коли користувач хоче кинути виклик традиційному способу викладу

### SCAMPER‑трансформація
Візьми стандартну математичну/технічну візуалізацію і трансформуй її:
- **Substitute**: заміни стандартну візуальну метафору (числова пряма → звивиста доріжка, матриця → міська сітка)
- **Combine**: об’єднай два підходи до пояснення (алгебраїчний + геометричний одночасно)
- **Reverse**: працюй у зворотному напрямку — почни з результату і розкладай його до аксіом
- **Modify**: перебільши параметр, щоб показати, чому він важливий (10 × швидкість навчання, 1000 × розмір вибірки)
- **Eliminate**: усунь усі позначення — пояснюй лише за допомогою анімації та просторових відносин

### Assumption Reversal
1. Перелічити, що є «стандартним» у візуалізації цієї теми (зліва направо, 2D, дискретні кроки, формальна нотація).
2. Вибрати найфундаментальніше припущення.
3. Змінити його (виведення справа наліво, 3D‑вбудовування 2D‑концепції, безперервна морфінг замість кроків, відсутність нотації).
4. Дослідити, що розкриття цього зворотного підходу показує, чого не видно у стандартному підході.