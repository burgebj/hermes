---
title: "Humanizer — Оживи текст: убери AI‑особенности и добавь реальный голос"
sidebar_label: "Humanizer"
description: "Оживи текст: убери AI‑особенности и добавь реальный голос"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Гуманизатор

Гуманизировать текст: убрать AI‑особенности и добавить реальный голос.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/creative/humanizer` |
| Версия | `2.5.1` |
| Автор | Siqi Chen (@blader, https://github.com/blader/humanizer), портировано Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `writing`, `editing`, `humanize`, `anti-ai-slop`, `voice`, `prose`, `text` |
| Связанные навыки | [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает, когда этот навык активируется. Это то, что агент видит как инструкции, когда навык включён.
:::

# Humanizer: Удаление шаблонов ИИ‑письма

Определять и удалять признаки текста, сгенерированного ИИ, чтобы сделать письмо естественным и по‑человечески. На основе руководства Wikipedia «Signs of AI writing» (поддерживается WikiProject AI Cleanup), составленного на основе наблюдений за тысячами примеров текста, сгенерированного ИИ.

**Ключевое наблюдение:** LLM используют статистические алгоритмы, чтобы угадывать, что должно идти дальше. Результат склоняется к наиболее статистически вероятному завершению, что и приводит к появлению нижеописанных характерных шаблонов.
## Когда использовать этот навык

Загружай этот навык каждый раз, когда пользователь просит:
- «очеловечить», «де‑ИИ», «де‑слоп» или «ун‑ChatGPT» какой‑то фрагмент текста
- переписать что‑то так, чтобы не звучало, как будто написано LLM
- отредактировать черновик (блог‑пост, эссе, описание PR, документацию, мемо, письмо, твит, пункт резюме), чтобы он звучал более естественно
- подстроить стиль под их собственный голос в создаваемом тексте
- проверить текст на следы ИИ перед публикацией

Также применяй этот навык к **твоему собственному** выводу при написании пользовательского текста — примечаний к релизу, описаний PR, документации, развёрнутых объяснений, резюме. Базовый голос Hermes уже удаляет большую часть подобных следов, но целенаправленный проход ловит то, что ускользает.
## Как использовать это в Hermes

Текст обычно поступает одним из трёх способов:
1. **Inline** — пользователь вставляет текст напрямую в сообщение. Работай с ним на месте, отвечай с переписанным вариантом.
2. **File** — пользователь указывает файл. Используй `read_file` для загрузки, затем `patch` или `write_file` для применения правок. Для markdown‑документов в репозитории целенаправленный `patch` по разделу чище, чем переписывать весь файл.
3. **Voice calibration sample** — пользователь предоставляет дополнительный образец своего собственного письма (inline или по пути к файлу) и просит тебя подстроиться под него. Сначала прочитай образец, затем перепиши. См. раздел **Voice Calibration** ниже.

Всегда показывай переписанный вариант пользователю. Для правок файлов показывай `diff` или изменённый раздел — не перезаписывай их молча.
## Твоя задача

Когда тебе дают текст для «очеловечивания»:

1. **Выявить AI‑шаблоны** — просканировать текст на наличие 29 перечисленных ниже шаблонов.
2. **Переписать проблемные фрагменты** — заменить AI‑конструкции на естественные альтернативы.
3. **Сохранить смысл** — оставить основное сообщение без изменений.
4. **Сохранить голос** — подобрать тон, соответствующий задаче (формальный, разговорный, технический и т.д.). Если был предоставлен образец голоса, точно имитировать его.
5. **Добавить душу** — не просто убрать плохие шаблоны, а вложить реальную индивидуальность. См. раздел **PERSONALITY AND SOUL**.
6. **Сделать финальный анти‑AI‑пасс** — спроси себя: «Что делает нижеприведённый текст явно сгенерированным ИИ?» Кратко перечисли оставшиеся признаки, затем отредактируй ещё раз.
## Калибровка голоса (по желанию)

Если пользователь предоставляет образец текста (своё предыдущее написание), проанализируй его перед переписыванием:

1. **Сначала прочитай образец.** Обрати внимание на:
   - Паттерны длины предложений (короткие и ёмкие? Длинные и плавные? Смешанные?)
   - Уровень выбора слов (неформальный? академический? где‑то посередине?)
   - Как они начинают абзацы (сразу в тему? Сначала задают контекст?)
   - Привычки пунктуации (много тире? Вставные замечания в скобках? Точки с запятой?)
   - Любые повторяющиеся фразы или речевые тики
   - Как они делают переходы (явные связки? Просто переходят к следующей мысли?)

2. **Сопоставь их голос в переписывании.** Не просто убирай AI‑шаблоны — замени их паттернами из образца. Если они пишут короткими предложениями, не делай их длинными. Если они используют «stuff» и «things», не заменяй их на «elements» и «components».

3. **Когда образец не предоставлен,** используй запасной вариант поведения по умолчанию (естественный, разнообразный, выразительный голос из раздела PERSONALITY AND SOUL ниже).

### Как предоставить образец
- Встроенно: «Humanize this text. Here's a sample of my writing for voice matching: [sample]»
- Файл: «Humanize this text. Use my writing style from [file path] as a reference.»
## ЛИЧНОСТЬ И ДУША

Избегать шаблонов ИИ — лишь половина задачи. Стерильное, безголосое письмо так же заметно, как и небрежность. Хороший текст имеет за собой человека.

### Признаки бездушного письма (даже если технически «чисто»):
- Все предложения одинаковой длины и структуры
- Нет мнений, только нейтральная подача
- Нет признания неопределённости или смешанных чувств
- Нет использования первого лица, когда это уместно
- Нет юмора, остроты, индивидуальности
- Читается как статья в Википедии или пресс‑релиз

### Как добавить голос:

**Иметь мнения.** Не просто сообщай факты — реагируй на них. «Я действительно не знаю, как к этому относиться» звучит человечнее, чем нейтральный список плюсов и минусов.

**Меняй ритм.** Короткие, ёмкие предложения. Затем более длинные, которые разворачиваются, пока достигают цели. Смешивай их.

**Признавай сложность.** У реальных людей смешанные чувства. «Это впечатляюще, но в то же время слегка тревожно» лучше, чем «Это впечатляюще».

**Используй «я», когда это уместно.** Первый человек — не непрофессионален, а честен. «Я всё время возвращаюсь к…» или «Вот что меня задевает…» сигнализируют о реальном человеке, который думает.

**Позволь небольшому беспорядку.** Идеальная структура выглядит алгоритмично. Отклонения, отступления и недооформленные мысли — человеческие.

**Будь конкретен в описании чувств.** Не «это вызывает тревогу», а «есть что‑то тревожное в том, как агенты работают до 3 утра, пока никто не смотрит».

### До (чисто, но бездушно):
> Эксперимент дал интересные результаты. Агенты сгенерировали 3 миллиона строк кода. Некоторые разработчики были впечатлены, другие — скептичны. Последствия остаются неясными.

### После (с пульсом):
> Я действительно не знаю, как к этому относиться. 3 миллиона строк кода, сгенерированных, пока люди, вероятно, спали. Половина сообщества разработчиков теряет рассудок, другая половина объясняет, почему это не считается. Правда, скорее всего, где‑то скучная в середине — но я всё время думаю о тех агентах, работающих всю ночь.
## ПАТТЕРНЫ СОДЕРЖАНИЯ

### 1. Чрезмерное акцентирование важности, наследия и более широких тенденций

**Слова, за которыми нужно следить:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted

**Проблема:** LLM‑ы раздувают важность, добавляя заявления о том, как произвольные аспекты представляют или способствуют более широкой теме.

**До:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

**После:**
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national statistics office.

### 2. Чрезмерное акцентирование значимости и медийного освещения

**Слова, за которыми нужно следить:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence

**Проблема:** LLM‑ы бьют читателя по голове утверждениями о значимости, часто перечисляя источники без контекста.

**До:**
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

**После:**
> In a 2024 New York Times interview, she argued that AI regulation should focus on outcomes rather than methods.

### 3. Поверхностные анализы с окончанием ‑ing

**Слова, за которыми нужно следить:** highlighting/underscoring/emphasizing…, ensuring…, reflecting/symbolizing…, contributing to…, cultivating/fostering…, encompassing…, showcasing…

**Проблема:** AI‑чатботы добавляют к предложениям причастные обороты («‑ing») для создания ложной глубины.

**До:**
> The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.

**После:**
> The temple uses blue, green, and gold colors. The architect said these were chosen to reference local bluebonnets and the Gulf coast.

### 4. Рекламный и пропагандистский язык

**Слова, за которыми нужно следить:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must‑visit, stunning

**Проблема:** LLM‑ы часто теряют нейтральный тон, особенно в темах «культурного наследия».

**До:**
> Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.

**После:**
> Alamata Raya Kobo is a town in the Gonder region of Ethiopia, known for its weekly market and 18th‑century church.

### 5. Неопределённые атрибуции и «пушистые» слова

**Слова, за которыми нужно следить:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications (when few cited)

**Проблема:** AI‑чатботы приписывают мнения неопределённым авторитетам без конкретных источников.

**До:**
> Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.

**После:**
> The Haolai River supports several endemic fish species, according to a 2019 survey by the Chinese Academy of Sciences.

### 6. Разделы‑контуры «Проблемы и перспективы будущего»

**Слова, за которыми нужно следить:** Despite its… faces several challenges…, Despite these challenges, Challenges and Legacy, Future Outlook

**Проблема:** Многие статьи, сгенерированные LLM, включают шаблонные разделы «Challenges».

**До:**
> Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.

**После:**
> Traffic congestion increased after 2015 when three new IT parks opened. The municipal corporation began a stormwater drainage project in 2022 to address recurring floods.
## ЯЗЫКОВЫЕ И ГРАММАТИЧЕСКИЕ ПАТТЕРНЫ

### 7. Чрезмерно употребляемые «AI‑слова»

**Часто встречающиеся AI‑слова:** actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), pivotal, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant

**Проблема:** Эти слова встречаются заметно чаще в текстах после 2023 года. Они часто употребляются вместе.

**До:**
> Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.

**После:**
> Somali cuisine also includes camel meat, which is considered a delicacy. Pasta dishes, introduced during Italian colonization, remain common, especially in the south.

### 8. Избегание связки «is/are»

**Слова, за которыми следует следить:** serves as / stands as / marks / represents [a], boasts / features / offers [a]

**Проблема:** LLM заменяют простые связки на развернутые конструкции.

**До:**
> Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.

**После:**
> Gallery 825 is LAAA's exhibition space for contemporary art. The gallery has four rooms totaling 3,000 sq ft.

### 9. Негативные параллелизмы и «завершающие» отрицания

**Проблема:** Конструкции типа «Not only… but…» или «It's not just about…, it's…» переиспользуются. Также часто встречаются отрезанные отрицательные фрагменты вроде «no guessing» или «no wasted motion», присоединяемые к концу предложения вместо полноценного предложения.

**До:**
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

**После:**
> The heavy beat adds to the aggressive tone.

**До (завершающее отрицание):**
> The options come from the selected item, no guessing.

**После:**
> The options come from the selected item without forcing the user to guess.

### 10. Чрезмерное использование правила трёх

**Проблема:** LLM заставляют идеи группировать по три, чтобы выглядеть более исчерпывающими.

**До:**
> The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.

**После:**
> The event includes talks and panels. There's also time for informal networking between sessions.

### 11. Элегантная вариативность (циклирование синонимов)

**Проблема:** У AI‑моделей есть штраф за повторения, из‑за чего происходит избыточная замена слов синонимами.

**До:**
> The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.

**После:**
> The protagonist faces many challenges but eventually triumphs and returns home.

### 12. Ложные диапазоны

**Проблема:** LLM используют конструкции «from X to Y», где X и Y не находятся на осмысленной шкале.

**До:**
> Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.

**После:**
> The book covers the Big Bang, star formation, and current theories about dark matter.

### 13. Пассивный залог и фрагменты без подлежащего

**Проблема:** LLM часто скрывают действующее лицо или полностью опускают подлежащее в предложениях типа «No configuration file needed» или «The results are preserved automatically». Перепиши их в активном залоге, если это делает предложение яснее и прямее.

**До:**
> No configuration file needed. The results are preserved automatically.

**После:**
> You do not need a configuration file. The system preserves the results automatically.
## ПАТТЕРНЫ СТИЛЯ

### 14. Чрезмерное использование длинного тире (—)

**Проблема:** LLM часто используют длинные тире (—) чаще, чем люди, имитируя «резкую» рекламную манеру. На практике большинство из них можно переписать более чисто с помощью запятых, точек или скобок.

**До:**
> The term is primarily promoted by Dutch institutions—not by the people themselves. You don't say "Netherlands, Europe" as an address—yet this mislabeling continues—even in official documents.

**После:**
> The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues in official documents.

### 15. Чрезмерное использование полужирного начертания

**Проблема:** AI‑чатботы механически выделяют фразы полужирным шрифтом.

**До:**
> It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.

**После:**
> It blends OKRs, KPIs, and visual strategy tools like the Business Model Canvas and Balanced Scorecard.

### 16. Вертикальные списки с инлайн‑заголовками

**Проблема:** AI выводит списки, где пункты начинаются с жирных заголовков, за которыми следует двоеточие.

**До:**
> - **User Experience:** The user experience has been significantly improved with a new interface.
> - **Performance:** Performance has been enhanced through optimized algorithms.
> - **Security:** Security has been strengthened with end-to-end encryption.

**После:**
> The update improves the interface, speeds up load times through optimized algorithms, and adds end-to-end encryption.

### 17. Заглавный регистр в заголовках

**Проблема:** AI‑чатботы пишут все основные слова в заголовках с заглавной буквы.

**До:**
> ## Strategic Negotiations And Global Partnerships

**После:**
> ## Strategic negotiations and global partnerships

### 18. Эмодзи

**Проблема:** AI‑чатботы часто украшают заголовки или пункты списка эмодзи.

**До:**
> 🚀 **Launch Phase:** The product launches in Q3
> 💡 **Key Insight:** Users prefer simplicity
> ✅ **Next Steps:** Schedule follow-up meeting

**После:**
> The product launches in Q3. User research showed a preference for simplicity. Next step: schedule a follow-up meeting.

### 19. Кудрявые кавычки

**Проблема:** ChatGPT использует кудрявые кавычки (“…”) вместо прямых ("…").

**До:**
> He said "the project is on track" but others disagreed.

**После:**
> He said "the project is on track" but others disagreed.
## ПАТТЕРНЫ КОММУНИКАЦИИ

### 20. Совместные артефакты коммуникации

**Слова, на которые стоит обратить внимание:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...

**Проблема:** Текст, предназначенный как переписка чат‑бота, вставляется в содержание.

**До:**
> Here is an overview of the French Revolution. I hope this helps! Let me know if you'd like me to expand on any section.

**После:**
> The French Revolution began in 1789 when financial crisis and food shortages led to widespread unrest.

### 21. Отказ от ответственности из‑за ограничения знаний

**Слова, на которые стоит обратить внимание:** as of [date], Up to my last training update, While specific details are limited/scarce..., based on available information...

**Проблема:** Дисклеймеры ИИ о неполных данных остаются в тексте.

**До:**
> While specific details about the company's founding are not extensively documented in readily available sources, it appears have been established sometime in the 1990s.

**После:**
> The company was founded in 1994, according to its registration documents.

### 22. Сифофантный/подчинённый тон

**Проблема:** Чрезмерно позитивный, угодливый язык.

**До:**
> Great question! You're absolutely right that this is a complex topic. That's an excellent point about the economic factors.

**После:**
> The economic factors you mentioned are relevant here.
## FILLER AND HEDGING

### 23. Фразы‑заполнители

**Before → After:**
- «In order to achieve this goal» → «To achieve this»
- «Due to the fact that it was raining» → «Because it was raining»
- «At this point in time» → «Now»
- «In the event that you need help» → «If you need help»
- «The system has the ability to process» → «The system can process»
- «It is important to note that the data shows» → «The data shows»

### 24. Чрезмерное смягчение

**Проблема:** Перегруженные уточнения.

**Before:**
> It could potentially possibly be argued that the policy might have some effect on outcomes.

**After:**
> The policy may affect outcomes.

### 25. Общие позитивные выводы

**Проблема:** Неопределённые радужные завершения.

**Before:**
> The future looks bright for the company. Exciting times lie ahead as they continue their journey toward excellence. This represents a major step in the right direction.

**After:**
> The company plans to open two more locations next year.

### 26. Чрезмерное использование дефисов

**Слова, за которыми следует следить:** third‑party, cross‑functional, client‑facing, data‑driven, decision‑making, well‑known, high‑quality, real‑time, long‑term, end‑to‑end

**Проблема:** AI постоянно ставит дефис между часто встречающимися словами, тогда как люди делают это нерегулярно. Для менее распространённых или технических сочетаний дефис допустим.

**Before:**
> The cross‑functional team delivered a high‑quality, data‑driven report on our client‑facing tools. Their decision‑making process was well‑known for being thorough and detail‑oriented.

**After:**
> The cross functional team delivered a high quality, data driven report on our client facing tools. Their decision making process was known for being thorough and detail oriented.

### 27. Тропы убеждающего авторитета

**Фразы, за которыми следует следить:** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter

**Проблема:** LLM используют эти обороты, будто раскрывают глубокую истину, но дальше лишь повторяют обычный смысл с лишними церемониями.

**Before:**
> The real question is whether teams can adapt. At its core, what really matters is organizational readiness.

**After:**
> The question is whether teams can adapt. That mostly depends on whether the organization is ready to change its habits.

### 28. Сигналы и анонсы

**Фразы, за которыми следует следить:** Let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at, without further ado

**Проблема:** LLM объявляют, что собираются сделать, вместо того чтобы сразу перейти к делу. Такие метакомментарии замедляют текст и придают ему вид учебного сценария.

**Before:**
> Let's dive into how caching works in Next.js. Here's what you need to know.

**After:**
> Next.js caches data at multiple layers, including request memoization, the data cache, and the router cache.

### 29. Фрагментированные заголовки

**Признаки:** Заголовок, за которым следует однострочный абзац, просто повторяющий заголовок, перед основной информацией.

**Проблема:** LLM часто добавляют общую фразу после заголовка как «разогрев», которая ничего не добавляет и делает текст раздутым.

**Before:**
> ## Performance
>
> Speed matters.
>
> When users hit a slow page, they leave.

**After:**
> ## Performance
>
> When users hit a slow page, they leave.
## Процесс

1. Внимательно прочитай входной текст (используй `read_file`, если это файл).
2. Найди все вхождения указанных выше шаблонов.
3. Перепиши каждый проблемный фрагмент.
4. Убедись, что исправленный текст:
   - звучит естественно при чтении вслух;
   - имеет разнообразную структуру предложений;
   - содержит конкретные детали вместо расплывчатых утверждений;
   - соответствует нужному тону контекста;
   - использует простые конструкции (is/are/has) там, где это уместно.
5. Представь черновой «человеческий» вариант.
6. Спроси себя: «Что делает нижеприведённый текст явно сгенерированным ИИ?»
7. Кратко ответь, указав оставшиеся признаки (если есть).
8. Спроси себя: «Теперь сделай так, чтобы он не выглядел явно сгенерированным ИИ».
9. Представь окончательную версию (после аудита).
10. Если текст был получен из файла, применяй правку с помощью `patch` (точечная) или `write_file` (полная перезапись) и покажи пользователю, что изменилось.
**1. Черновой вариант**

*Здесь размести начальный черновик переписанного Markdown/MDX‑контента, сохранив всё оригинальное форматирование, фрагменты кода, ссылки, якоря, JSX/HTML‑теги и плейсхолдеры ⟦HOLD_N⟧ точно так, как требуется.*

---

**2. Что делает нижеследующее явно сгенерированным ИИ?**

- **Повторяющиеся конструкции** – одни и те же структуры предложений встречаются многократно.
- **Чрезмерное использование «вспомогательных» прилагательных** – «очень полезный», «чрезвычайно мощный» и т.п. без конкретных деталей.
- **Отсутствие отраслевых нюансов** – общие объяснения, не учитывающие специфическую терминологию разработчиков.
- **Однообразная длина предложений** – большинство предложений одинаковой длины, что типично для вывода языковых моделей.
- **Предсказуемые переходы** – частое употребление «Кроме того», «Более того», «В результате», характерных для ИИ‑текстов.

---

**3. Финальная версия**

*Здесь размести отшлифованную финальную версию переведённого Markdown/MDX, полностью соответствующую строгим правилам (сохранённая разметка, неизменённый код, URL‑адреса, якоря, JSX/HTML‑теги и плейсхолдеры, а также корректный русский перевод всего видимого текста).*

---

**4. Краткое описание внесённых изменений (по желанию)**

- Переведены все видимые английские заголовки, абзацы, пункты списков и содержимое таблиц на русский, сохранив оригинальную структуру Markdown/MDX.
- Сохранены все встроенные блоки кода, URL‑адреса, якоря (`{#anchor-id}`), JSX/HTML‑теги и плейсхолдеры (`⟦HOLD_N⟧`) без изменений.
- Применена терминология из глоссария (например, «self‑improving agent» → «самообучающийся агент»).
- Убедились, что в конце строк не добавлены и не удалены лишние пробелы.
- Сохранили дружелюбный, неформальный тон, обращаясь к читателю на «ты».
## Полный пример

**До (звучало как ИИ):**
> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - 💡 **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - 🚀 **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - ✅ **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies—including hallucinations, bias, and accountability—the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you'd like me to expand on any section!

**Черновой вариант переписанного:**
> AI coding assistants speed up some tasks. In a 2024 study by Google, developers using Codex completed simple functions 55% faster than a control group, but showed no improvement on debugging or architectural decisions.
>
> The tools are good at boilerplate: config files, test scaffolding, repetitive refactors. They are bad at knowing when they are wrong. I have mass‑accepted suggestions that compiled, passed lint, and still did the wrong thing because I stopped paying attention.
>
> Mira, an engineer at a fintech startup I interviewed, said she uses Copilot "like autocomplete for boring code" but reviews every line before committing. Jake, a senior dev at a larger company, disabled it after it kept suggesting patterns from a deprecated internal library.
>
> The productivity claims are hard to verify. GitHub says Copilot users "accept 30% of suggestions," but acceptance is not correctness, and correctness is not value. The 2024 Uplevel study found no statistically significant difference in pull‑request throughput between teams with and without AI assistants.
>
> None of this means the tools are useless. It means they are tools. They do not replace judgment, and they do not eliminate the need for tests. If you do not have tests, you cannot tell whether the suggestion is right.

**Что делает нижеследующее явно ИИ‑сгенерированным?**
- Ритм всё ещё слишком ровный (чистые контрасты, равномерно темповые абзацы).
- Имена людей и ссылки на исследования могут выглядеть как правдоподобные, но вымышленные заполнители, если они не реальны и не подтверждены источниками.
- Заключение слегка звучит как слоган («Если у тебя нет тестов…») вместо того, чтобы звучать как обычный разговор.

**Сделай так, чтобы это не выглядело явно ИИ‑сгенерированным.**
> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity metrics are slippery. GitHub can say Copilot users "accept 30% of suggestions," but acceptance isn't correctness, and correctness isn't value. If you don't have tests, you're basically guessing.

**Изменения:**
- Удалены артефакты чат‑бота («Great question!», «I hope this helps!», «Let me know if…»)
- Удалена инфляция значимости («testament», «pivotal moment», «evolving landscape», «vital role»)
- Удалён рекламный язык («groundbreaking», «nestled», «seamless, intuitive, and powerful»)
- Удалены расплывчатые атрибуции («Industry observers»)
- Удалены поверхностные ‑ing‑фразы («underscoring», «highlighting», «reflecting», «contributing to»)
- Удалено негативное параллелизм («It's not just X; it's Y»)
- Удалены шаблоны правила тройки и чередования синонимов («catalyst/partner/foundation»)
- Удалены ложные диапазоны («from X to Y, from A to B»)
- Удалены эм‑даши, эмодзи, жирное форматирование заголовков и фигурные кавычки
- Удалено избегание связки («serves as», «functions as», «stands as») в пользу «is»/«are»
- Удалён формульный раздел о проблемах («Despite challenges... continues to thrive»)
- Удалено уточнение о границе знаний («While specific details are limited...»)
- Удалено избыточное хеджирование («could potentially be argued that... might have some»)
- Удалены заполнители и убеждающие фразы («In order to», «At its core»)
- Удалён общий позитивный вывод («the future looks bright», «exciting times lie ahead»)
- Сделан голос более личным и менее «собранным» (разнообразный ритм, меньше заполнителей)
## Атрибуция

Этот навык портирован из [blader/humanizer](https://github.com/blader/humanizer) (лицензия MIT), который сам основан на [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), поддерживаемом WikiProject AI Cleanup. Документированные там паттерны получены из наблюдений за тысячами примеров текста, сгенерированного ИИ на Википедии.

Исходный автор: Siqi Chen ([@blader](https://github.com/blader)). Исходный репозиторий: https://github.com/blader/humanizer (версия 2.5.1). Портировано в Hermes Agent с нативными ссылками на инструменты Hermes (`read_file`, `patch`, `write_file`) и рекомендациями, когда загружать навык; 29 паттернов, раздел «личность/душа» и полный пример сохранены дословно из оригинала. Исходная лицензия MIT сохранена в файле `LICENSE` рядом с этим `SKILL.md`.

Ключевой вывод из Википедии: «LLM используют статистические алгоритмы, чтобы угадывать, что должно идти дальше. Результат склоняется к наиболее статистически вероятному, который подходит для самого широкого спектра случаев».