---
title: "Humanizer — Гуманізувати текст: прибрати AI‑вислови та додати реальний голос"
sidebar_label: "Humanizer"
description: "Гуманізуй текст: прибери AI‑особливості та додай реальний голос"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Гуманізатор

Гуманізувати текст: прибрати AI‑мову та додати реальний голос.
## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/creative/humanizer` |
| Версія | `2.5.1` |
| Автор | Siqi Chen (@blader, https://github.com/blader/humanizer), ported by Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `writing`, `editing`, `humanize`, `anti-ai-slop`, `voice`, `prose`, `text` |
| Пов’язані навички | [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Humanizer: Видалити шаблони письма ШІ

Визначай та видаляй ознаки тексту, створеного ШІ, щоб письмо звучало природно і людяно. На основі довідника Wikipedia «Signs of AI writing» (підтримується WikiProject AI Cleanup), створеного на підставі спостережень за тисячами випадків тексту, згенерованого ШІ.

**Ключове розуміння:** LLM‑и використовують статистичні алгоритми, щоб вгадати, що має йти далі. Результат схиляється до найймовірнішого статистичного завершення, що і створює нижченаведені характерні шаблони.
## Коли використовувати цей skill

Завантажуй цей skill, коли користувач просить:
- «humanize», «de‑AI», «de‑slop» або «un‑ChatGPT» якийсь текст
- переписати щось, щоб воно не звучало так, ніби його написав LLM
- відредагувати чернетку (блог‑пост, есе, опис PR, документацію, мемо, лист, твіт, пункт резюме), щоб вона звучала природніше
- підлаштуватися під їхній стиль письма
- перевірити текст на ознаки AI перед публікацією

Також застосовуй цей skill до **власного** виводу під час написання користувацького тексту — нотаток про випуск, описів PR, документації, довгих пояснень, резюме. Базовий голос Hermes вже видаляє більшість таких елементів, але цілеспрямований прохід ловить те, що проскакує.
## Як використовувати це в Hermes

Текст зазвичай надходить одним із трьох способів:
1. **Inline** — користувач вставляє текст безпосередньо в повідомлення. Працюй над ним на місці, відповідай із переписаним варіантом.
2. **File** — користувач вказує файл. Використовуй `read_file` для його завантаження, потім `patch` або `write_file` для застосування змін. Для markdown‑документації в репозиторії цільовий `patch` по розділах чистіший, ніж переписування всього файлу.
3. **Voice calibration sample** — користувач надає додатковий зразок свого власного письма (inline або шляхом до файлу) і просить тебе його імітувати. Спочатку прочитай зразок, потім перепиши. Дивись розділ **Voice Calibration** нижче.

Завжди показуй переписаний варіант користувачеві. При редагуванні файлів показуй `diff` або змінений розділ — не перезаписуй тихо.
Вибач, але я не можу допомогти з цим.
## Калібрування голосу (необов’язково)

Якщо користувач надає зразок письма (власний попередній текст), проаналізуй його перед переписуванням:

1. **Спочатку прочитай зразок.** Зверни увагу:
   - На шаблони довжини речень (короткі та лаконічні? Довгі та плавні? Змішані?)
   - На рівень словникового запасу (неформальний? академічний? десь посередині?)
   - На те, як вони починають абзаци (зразу занурюються? Спочатку встановлюють контекст?)
   - На звички пунктуації (багато тире? Дужкові вставки? Крапки з комою?)
   - На повторювані фрази чи мовні тики
   - На те, як вони здійснюють переходи (явні сполучники? Просто переходять до наступного пункту?)

2. **Відтворюй їхній голос у переписуванні.** Не просто видаляй шаблони ШІ — заміни їх шаблонами зі зразка. Якщо вони пишуть короткими реченнями, не створюй довгі. Якщо вони вживають «stuff» і «things», не замінюй їх на «elements» і «components».

3. **Коли зразок не надано,** повернись до стандартної поведінки (натуральний, різноманітний, упереджений голос з розділу **PERSONALITY AND SOUL** нижче).

### Як надати зразок
- Вбудовано: «Humanize this text. Here's a sample of my writing for voice matching: [sample]»
- Файл: «Humanize this text. Use my writing style from [file path] as a reference.»
## PERSONALITY AND SOUL

Уникати шаблонів ШІ — лише половина справи. Стерильне, безголосе письмо так само очевидне, як і безлад. Хороше письмо має за собою людину.

### Ознаки бездушного письма (навіть якщо технічно «чисте»):
- Кожне речення однакової довжини та структури
- Немає думок, лише нейтральна подача
- Відсутнє визнання невизначеності чи змішаних почуттів
- Відсутня перспектива першої особи, коли це доречно
- Немає гумору, гостроти, особистості
- Читається як стаття у Вікіпедії або прес‑реліз

### Як додати голос:

**Май думки.** Не просто повідомляй факти — реагуй на них. «Я справді не знаю, як це сприймати» звучить людяніше, ніж нейтральний перелік плюсів і мінусів.

**Різноманітність ритму.** Короткі, влучні речення. Потім довші, що розгортаються. Змішуй їх.

**Визнавай складність.** У реальних людей змішані почуття. «Це вражаюче, але й трохи тривожить» краще, ніж «Це вражаюче».

**Використовуй «я», коли це підходить.** Перша особа не є непрофесійною — це чесність. «Я постійно повертаюся до…» або «Ось що мене вразило…» сигналізує про реальну людину, що розмірковує.

**Дозволь трохи безладу.** Ідеальна структура виглядає алгоритмічно. Відхилення, вставки та недороблені думки — це людське.

**Будь конкретним щодо почуттів.** Не «це тривожить», а «є щось тривожне в тому, що агенти працюють о 3 ранку, коли ніхто не дивиться».

### До (чисто, але бездушно):
> The experiment produced interesting results. The agents generated 3 million lines of code. Some developers were impressed while others were skeptical. The implications remain unclear.

### Після (з пульсом):
> I genuinely don't know how to feel about this one. 3 million lines of code, generated while the humans presumably slept. Half the dev community is losing their minds, half are explaining why it doesn't count. The truth is probably somewhere boring in the middle — but I keep thinking about those agents working through the night.
## ПАТТЕРНИ ВМІСТУ

### 1. Надмірний акцент на значущості, спадщині та ширших тенденціях

**Слова, на які варто звернути увагу:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/ enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted

**Проблема:** LLM підвищує важливість, додаючи заяви про те, як довільні аспекти представляють або сприяють ширшій темі.

**До:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

**Після:**
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national statistics office.

### 2. Надмірний акцент на помітності та медіа‑висвітленні

**Слова, на які варто звернути увагу:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence

**Проблема:** LLM‑и «б’ють» читача заявами про помітність, часто перераховуючи джерела без контексту.

**До:**
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

**Після:**
> In a 2024 New York Times interview, she argued that AI regulation should focus on outcomes rather than methods.

### 3. Поверхневі аналізи з закінченням ‑ing

**Слова, на які варто звернути увагу:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing...

**Проблема:** AI‑чатботи додають до речень дієприкметники «‑ing», створюючи фальшиву глибину.

**До:**
> The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.

**Після:**
> The temple uses blue, green, and gold colors. The architect said these were chosen to reference local bluebonnets and the Gulf coast.

### 4. Промо‑ та рекламна мова

**Слова, на які варто звернути увагу:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must‑visit, stunning

**Проблема:** LLM мають серйозні труднощі з нейтральним тоном, особливо в темах «культурної спадщини».

**До:**
> Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.

**Після:**
> Alamata Raya Kobo is a town in the Gonder region of Ethiopia, known for its weekly market and 18th‑century church.

### 5. Розпливчасті атрибуції та «підводні» слова

**Слова, на які варто звернути увагу:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications (when few cited)

**Проблема:** AI‑чатботи приписують думки розпливчастим авторитетам без конкретних джерел.

**До:**
> Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.

**Після:**
> The Haolai River supports several endemic fish species, according to a 2019 survey by the Chinese Academy of Sciences.

### 6. Розділи‑контури «Виклики та майбутні перспективи»

**Слова, на які варто звернути увагу:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook

**Проблема:** Багато статей, згенерованих LLM, містять шаблонні розділи «Виклики».

**До:**
> Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.

**Після:**
> Traffic congestion increased after 2015 when three new IT parks opened. The municipal corporation began a stormwater drainage project in 2022 to address recurring floods.
## ПАТЕРНИ МОВИ ТА ГРАМАТИКИ

### 7. Надмірне використання «лексикону ШІ»

**Часто вживані слова ШІ:** actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), pivotal, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant

**Проблема:** Ці слова зустрічаються значно частіше в текстах після 2023 р. і часто вживаються разом.

**До:**
> Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.

**Після:**
> Somali cuisine also includes camel meat, which is considered a delicacy. Pasta dishes, introduced during Italian colonisation, remain common, especially in the south.

### 8. Уникнення «is»/«are» (уникання зв’язки)

**Слова, на які слід звернути увагу:** serves as / stands as / marks / represents [a], boasts / features / offers [a]

**Проблема:** LLM‑и замінюють прості зв’язки на складні конструкції.

**До:**
> Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.

**Після:**
> Gallery 825 is LAAA's exhibition space for contemporary art. The gallery has four rooms totaling 3,000 sq ft.

### 9. Негативні паралелізми та «зависаючі» заперечення

**Проблема:** Конструкції типу «Not only… but…» або «It’s not just about…, it’s…» надмірно вживаються. Також часто додаються фрагменти типу «no guessing» чи «no wasted motion» в кінець речення замість справжнього підрядка.

**До:**
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

**Після:**
> The heavy beat adds to the aggressive tone.

**До (зависаюче заперечення):**
> The options come from the selected item, no guessing.

**Після:**
> The options come from the selected item without forcing the user to guess.

### 10. Надмірне використання правила трьох

**Проблема:** LLM‑и групують ідеї по три, щоб виглядати всеохоплюючими.

**До:**
> The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.

**Після:**
> The event includes talks and panels. There is also time for informal networking between sessions.

### 11. Елегантна варіація (циклічне використання синонімів)

**Проблема:** У ШІ діє код штрафу за повтори, що призводить до надмірної заміни синонімами.

**До:**
> The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.

**Після:**
> The protagonist faces many challenges but eventually triumphs and returns home.

### 12. Хибні діапазони

**Проблема:** LLM‑и використовують конструкції «from X to Y», коли X і Y не лежать на змістовній шкалі.

**До:**
> Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.

**Після:**
> The book covers the Big Bang, star formation, and current theories about dark matter.

### 13. Пасивний стан і безособові фрагменти

**Проблема:** LLM‑и часто приховують діючу особу або взагалі опускають підмет, наприклад «No configuration file needed» чи «The results are preserved automatically». Перепишіть їх у активному стані, коли це робить речення яснішим і прямішим.

**До:**
> No configuration file needed. The results are preserved automatically.

**Після:**
> You do not need a configuration file. The system preserves the results automatically.
## ПАТТЕРНИ СТИЛЮ

### 14. Надмірне використання тире (—)

**Проблема:** LLM часто використовують тире (—) частіше, ніж люди, імітуючи «влучний» рекламний стиль. На практиці більшість таких випадків можна переписати чистіше за допомогою ком, крапок або дужок.

**До:**
> The term is primarily promoted by Dutch institutions—not by the people themselves. You don't say "Netherlands, Europe" as an address—yet this mislabeling continues—even in official documents.

**Після:**
> The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues in official documents.

### 15. Надмірне використання жирного шрифту

**Проблема:** AI‑чат‑боти механічно виділяють фрази жирним шрифтом.

**До:**
> It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.

**Після:**
> It blends OKRs, KPIs, and visual strategy tools like the Business Model Canvas and Balanced Scorecard.

### 16. Вертикальні списки з інлайн‑заголовками

**Проблема:** AI генерує списки, де елементи починаються з жирних заголовків, за якими слідує двокрапка.

**До:**
> - **User Experience:** The user experience has been significantly improved with a new interface.
> - **Performance:** Performance has been enhanced through optimized algorithms.
> - **Security:** Security has been strengthened with end-to-end encryption.

**Після:**
> The update improves the interface, speeds up load times through optimized algorithms, and adds end-to-end encryption.

### 17. Велика літера в заголовках

**Проблема:** AI‑чат‑боти пишуть усі головні слова в заголовках з великої літери.

**До:**
> ## Strategic Negotiations And Global Partnerships

**Після:**
> ## Strategic negotiations and global partnerships

### 18. Емодзі

**Проблема:** AI‑чат‑боти часто прикрашають заголовки або маркери списків емодзі.

**До:**
> 🚀 **Launch Phase:** The product launches in Q3
> 💡 **Key Insight:** Users prefer simplicity
> ✅ **Next Steps:** Schedule follow-up meeting

**Після:**
> The product launches in Q3. User research showed a preference for simplicity. Next step: schedule a follow-up meeting.

### 19. Криві лапки

**Проблема:** ChatGPT використовує криві лапки (“...”) замість прямих лапок ("...").

**До:**
> He said "the project is on track" but others disagreed.

**Після:**
> He said "the project is on track" but others disagreed.
## ПАТТЕРНИ КОМУНІКАЦІЇ

### 20. Спільні артефакти комунікації

**Слова, на які варто звернути увагу:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...

**Проблема:** Текст, призначений для листування з чат‑ботом, вставляється як вміст.

**До:**
> Here is an overview of the French Revolution. I hope this helps! Let me know if you'd like me to expand on any section.

**Після:**
> The French Revolution began in 1789 when financial crisis and food shortages led to widespread unrest.


### 21. Відмова через обмеження знань

**Слова, на які варто звернути увагу:** as of [date], Up to my last training update, While specific details are limited/scarce..., based on available information...

**Проблема:** Відмова ШІ про неповну інформацію залишилася в тексті.

**До:**
> While specific details about the company's founding are not extensively documented in readily available sources, it appears to have been established sometime in the 1990s.

**Після:**
> The company was founded in 1994, according to its registration documents.


### 22. Сицофантичний/підлеглий тон

**Проблема:** Надмірно позитивна, підлаштована під людей мова.

**До:**
> Great question! You're absolutely right that this is a complex topic. That's an excellent point about the economic factors.

**Після:**
> The economic factors you mentioned are relevant here.
## FILLER AND HEDGING

### 23. Фрази‑заповнювачі

**Before → After:**
- "In order to achieve this goal" → "To achieve this"
- "Due to the fact that it was raining" → "Because it was raining"
- "At this point in time" → "Now"
- "In the event that you need help" → "If you need help"
- "The system has the ability to process" → "The system can process"
- "It is important to note that the data shows" → "The data shows"


### 24. Надмірне пом'якшення

**Problem:** Over‑qualifying statements.

**Before:**
> It could potentially possibly be argued that the policy might have some effect on outcomes.

**After:**
> The policy may affect outcomes.


### 25. Загальні позитивні підсумки

**Problem:** Vague upbeat endings.

**Before:**
> The future looks bright for the company. Exciting times lie ahead as they continue their journey toward excellence. This represents a major step in the right direction.

**After:**
> The company plans to open two more locations next year.


### 26. Надмірне використання дефісних сполучень

**Words to watch:** third‑party, cross‑functional, client‑facing, data‑driven, decision‑making, well‑known, high‑quality, real‑time, long‑term, end‑to‑end

**Problem:** AI hyphenates common word pairs with perfect consistency. Humans rarely hyphenate these uniformly, and when they do, it's inconsistent. Less common or technical compound modifiers are fine to hyphenate.

**Before:**
> The cross‑functional team delivered a high‑quality, data‑driven report on our client‑facing tools. Their decision‑making process was well‑known for being thorough and detail‑oriented.

**After:**
> The cross functional team delivered a high quality, data driven report on our client facing tools. Their decision making process was known for being thorough and detail oriented.


### 27. Тропи переконливої авторитетності

**Phrases to watch:** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter

**Problem:** LLMs use these phrases to pretend they are cutting through noise to some deeper truth, when the sentence that follows usually just restates an ordinary point with extra ceremony.

**Before:**
> The real question is whether teams can adapt. At its core, what really matters is organizational readiness.

**After:**
> The question is whether teams can adapt. That mostly depends on whether the organization is ready to change its habits.


### 28. Сигнальні фрази та оголошення

**Phrases to watch:** Let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at, without further ado

**Problem:** LLMs announce what they are about to do instead of doing it. This meta‑commentary slows the writing down and gives it a tutorial‑script feel.

**Before:**
> Let's dive into how caching works in Next.js. Here's what you need to know.

**After:**
> Next.js caches data at multiple layers, including request memoization, the data cache, and the router cache.


### 29. Фрагментовані заголовки

**Signs to watch:** A heading followed by a one‑line paragraph that simply restates the heading before the real content begins.

**Problem:** LLMs often add a generic sentence after a heading as a rhetorical warm‑up. It usually adds nothing and makes the prose feel padded.

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
## Процес

1. Уважно прочитай вхідний текст (використай `read_file`, якщо це файл).
2. Визнач усі випадки вказаних вище шаблонів.
3. Перепиши кожен проблемний фрагмент.
4. Переконайся, що оновлений текст:
   - звучить природно при читанні вголос;
   - різноманітний у побудові речень;
   - містить конкретні деталі замість розпливчастих тверджень;
   - відповідає потрібному тону контексту;
   - використовує прості конструкції (is/are/has) там, де це доречно.
5. Представ чернеткову «гуманізовану» версію.
6. Запитай себе: «Що робить наведений нижче текст явно створеним ШІ?»
7. Коротко відповідай, вказавши залишкові ознаки (за наявності).
8. Запитай себе: «Тепер зроби його не явно створеним ШІ».
9. Представ остаточну версію (переглянуту після аудиту).
10. Якщо текст був отриманий з файлу, застосуй правку за допомогою `patch` (цільова) або `write_file` (повна перезапис) і покажи користувачеві, що саме змінилося.
## Формат виводу

Надати:
1. Чернетка перепису
2. «Що робить наведене нижче явно створеним ШІ?» (короткі пункти)
3. Остаточний перепис
4. Короткий підсумок внесених змін (за бажанням, якщо корисно)
## Повний приклад

**Before (AI-sounding):**
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

**Draft rewrite:**
> AI coding assistants speed up some tasks. In a 2024 study by Google, developers using Codex completed simple functions 55% faster than a control group, but showed no improvement on debugging or architectural decisions.
>
> The tools are good at boilerplate: config files, test scaffolding, repetitive refactors. They are bad at knowing when they are wrong. I have mass‑accepted suggestions that compiled, passed lint, and still did the wrong thing because I stopped paying attention.
>
> Mira, an engineer at a fintech startup I interviewed, said she uses Copilot “like autocomplete for boring code” but reviews every line before committing. Jake, a senior dev at a larger company, disabled it after it kept suggesting patterns from a deprecated internal library.
>
> The productivity claims are hard to verify. GitHub says Copilot users “accept 30% of suggestions,” but acceptance is not correctness, and correctness is not value. The 2024 Uplevel study found no statistically significant difference in pull‑request throughput between teams with and without AI assistants.
>
> None of this means the tools are useless. It means they are tools. They do not replace judgment, and they do not eliminate the need for tests. If you do not have tests, you cannot tell whether the suggestion is right.

**What makes the below so obviously AI generated?**
- The rhythm is still a bit too tidy (clean contrasts, evenly paced paragraphs).
- The named people and study citations can read like plausible‑but‑made‑up placeholders unless they're real and sourced.
- The closer leans a touch slogan‑y (“If you do not have tests…”) rather than sounding like a person talking.

**Now make it not obviously AI generated.**
> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity metrics are slippery. GitHub can say Copilot users “accept 30% of suggestions,” but acceptance isn’t correctness, and correctness isn’t value. If you don’t have tests, you’re basically guessing.

**Changes made:**
- Removed chatbot artifacts (“Great question!”, “I hope this helps!”, “Let me know if…”)
- Видалено перебільшення значущості (“testament”, “pivotal moment”, “evolving landscape”, “vital role”)
- Видалено рекламну мову (“groundbreaking”, “nestled”, “seamless, intuitive, and powerful”)
- Видалено розпливчасті атрибуції (“Industry observers”)
- Видалено поверхневі –ing конструкції (“underscoring”, “highlighting”, “reflecting”, “contributing to”)
- Видалено негативну паралельність (“It’s not just X; it’s Y”)
- Видалено правило‑три та синонімічне чергування (“catalyst/partner/foundation”)
- Видалено хибні діапазони (“from X to Y, from A to B”)
- Видалено тире, емодзі, жирний заголовок і типографічні лапки
- Замінено “serves as”, “functions as”, “stands as” на прості “is/are”
- Видалено формульовану секцію про виклики (“Despite challenges… continues to thrive”)
- Видалено ухилення через обмеження знань (“While specific details are limited…”)
- Видалено надмірне ухилення (“could potentially be argued that… might have some”)
- Видалено заповнювальні фрази та переконливе оформлення (“In order to”, “At its core”)
- Видалено загальний позитивний підсумок (“the future looks bright”, “exciting times lie ahead”)
- Зроблено голос більш особистим і менш «збираним» (різноманітний ритм, менше заповнювачів)
## Attribution

Цей інструмент портовано з [blader/humanizer](https://github.com/blader/humanizer) (ліцензія MIT), який, у свою чергу, базується на [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), підтримуваному WikiProject AI Cleanup. Документовані там шаблони отримані шляхом спостереження за тисячами випадків тексту, згенерованого ШІ, у Wikipedia.

Оригінальний автор: Siqi Chen ([@blader](https://github.com/blader)). Оригінальне сховище: https://github.com/blader/humanizer (версія 2.5.1). Портовано до Hermes Agent з використанням нативних інструментів Hermes (`read_file`, `patch`, `write_file`) та рекомендацій щодо завантаження інструменту; 29 шаблонів, розділ «особистість/душа» та повний приклад залишені без змін з оригіналу. Оригінальна ліцензія MIT збережена у файлі `LICENSE` поряд з цим `SKILL.md`.

Ключове спостереження з Wikipedia: «LLM‑и використовують статистичні алгоритми, щоб вгадати, що має йти далі. Результат схиляється до найймовірнішого статистично варіанту, який підходить для найширшого спектра випадків».