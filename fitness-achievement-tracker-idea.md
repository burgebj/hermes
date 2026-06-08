# Fitness Achievement Tracker / Goal Achievement Engine

## Source

This document captures the original voice-message transcripts and the product idea that emerged from the conversation.

## Original transcripts

### Transcript 1

> I just kind of got an idea and for now let's say I'm making a habit tracker but more of a fitness tracker and if this is already there then maybe it's not even worth bothering but it'd be a fun app to develop. So you create your own goals or achievements and then automatically use your phone's help a lot of so for example the mega is to run a 5k right so create that goal and then once I do it then bam with season a lot but then now that becomes a two or two there where now you need to run let's say two or five 5k to level it up so you can create the let's say achievements for your fitness goals and maybe it doesn't have to be limited to fitness but fitness is the idea I have right now because I want to like run a 5k I want to run a 5k and under x minutes I want to walk x amount of kilometers per week per month now not every goal needs to level up like you know walking x amount of kilometers per or week that could just be a set goal right but other goals can be you know tearable and then the the ones that are set goals can just upgrade every time you achieve them right like walk 10 kilometers per week then the next time once you do that five times you achieve here two two three etc there's this sound like a solid idea

### Transcript 2

> Okay, he didn't quite capture my idea, but maybe there should be both where one achievement is run a 5k once, right? But another type of achievement or goal is run a 5k once, a tier goal. Once you run it once, it upgrades, and they have to run a 5k five times, nice tier two. And then once you do it five times, maybe it's 10, and then maybe 20, 25, 50, and you keep going up in tiers.

### Transcript 3

> And then while we're starting with fitness goals, because that's where my mindset is right now, it could be a different, it doesn't have to be limited to fitness, right? It could be also hydration tracking. It could be reading books, saving money, I don't know. It could be like a goal-based app. I definitely think the start is gonna be fitness.

## Core idea

A goal-based achievement app that starts with fitness, where users create their own achievements and the app automatically verifies progress using phone/watch health data where possible.

The app is not just a habit tracker. The key mechanic is that goals can behave like video-game achievements:

- Some achievements are completed once and stay complete.
- Some achievements are tiered and upgrade after completion.
- Some goals are recurring, such as weekly or monthly targets.
- Some recurring goals can also contribute to long-term achievement tiers.

The first wedge is fitness because it has strong automatic data sources through Apple Health, phone sensors, and wearables. Longer term, the underlying system could expand into a broader life-goal achievement engine covering hydration, reading, saving money, learning, and other self-improvement goals.

## Product positioning

Possible positioning:

> Custom fitness achievements powered by Apple Health.

Broader positioning:

> A personal achievement system for real-life goals.

Another framing:

> Xbox-style achievements for your body and your life.

The important distinction is that the user creates the achievement rules, and the app tracks/levels them automatically where integrations allow.

## Achievement mechanics

### 1. One-shot achievements

A goal that completes once and is done.

Examples:

- Run a 5K once.
- Walk 20km in one day.
- Complete your first workout.
- Hit 10,000 steps in a day.
- Read one book.
- Save $100.

### 2. Tiered achievements

A goal that upgrades after completion. The same core achievement continues, but each tier requires more repetitions or a harder threshold.

Example: **Run a 5K**

- Tier 1: Run a 5K once.
- Tier 2: Run a 5K 5 times.
- Tier 3: Run a 5K 10 times.
- Tier 4: Run a 5K 20 times.
- Tier 5: Run a 5K 25 times.
- Tier 6: Run a 5K 50 times.
- Later tiers can continue indefinitely or follow a defined progression.

This is the core mechanic: after you complete a goal, the app gives you the next version of it.

### 3. Performance tier achievements

A tiered goal based on improving performance rather than repeating the same activity.

Example: **5K time goal**

- Tier 1: Run 5K under 40 minutes.
- Tier 2: Run 5K under 35 minutes.
- Tier 3: Run 5K under 30 minutes.
- Tier 4: Run 5K under 25 minutes.
- Tier 5: Run 5K under 20 minutes.

### 4. Recurring goals

A goal that resets on a schedule.

Examples:

- Walk 10km per week.
- Run 20km per month.
- Drink 2L of water per day.
- Read 30 minutes per day.
- Save $50 per week.

### 5. Recurring + tiered goals

A recurring goal that contributes to long-term tiers.

Example: **Walk 10km per week**

- Weekly goal: walk 10km this week.
- Tier 1: complete the weekly goal once.
- Tier 2: complete it 5 times.
- Tier 3: complete it 10 times.
- Tier 4: complete it 25 times.
- Tier 5: complete it 52 times.

This allows a repeated habit to generate a sense of long-term progression.

## Fitness-first examples

### Run a 5K

Type: tiered achievement

- Tier 1: Run 5K once.
- Tier 2: Run 5K 5 times.
- Tier 3: Run 5K 10 times.
- Tier 4: Run 5K 25 times.
- Tier 5: Run 5K 50 times.

Data source: Apple Health workouts / running distance.

### Run a faster 5K

Type: performance tier achievement

- Tier 1: Run 5K under 40 minutes.
- Tier 2: Run 5K under 35 minutes.
- Tier 3: Run 5K under 30 minutes.
- Tier 4: Run 5K under 25 minutes.

Data source: Apple Health workout distance + duration.

### Walk weekly distance

Type: recurring + tiered goal

- Weekly target: Walk 10km in a week.
- Tier progression: Complete this 1 / 5 / 10 / 25 / 52 weeks.

Data source: Apple Health walking/running distance or steps converted to distance.

## Non-fitness expansion ideas

The app can eventually support other categories, but these may require manual tracking or integrations.

### Hydration

- Drink 2L of water today.
- Drink 2L daily for 7 / 30 / 100 days.
- Log water intake 5 days in a week.

Data source: manual entry or Apple Health nutrition/water data.

### Reading

- Read one book.
- Read 5 / 10 / 25 / 50 books.
- Read 30 minutes per day for 7 / 30 / 100 days.

Data source: manual entry, Goodreads/Kindle integration later, or timer-based tracking.

### Saving money

- Save $100.
- Save $500 / $1,000 / $5,000.
- Save $50 per week for 4 / 12 / 52 weeks.

Data source: manual entry first; banking integrations later only if worth it.

### Learning

- Complete one course.
- Study 5 / 10 / 25 / 100 hours.
- Practice a skill 30 minutes per day for 7 / 30 / 100 days.

Data source: manual entry or timer.

## Suggested MVP

The MVP should stay narrow enough to build, but still prove the main mechanic.

### MVP scope

- iOS app.
- Apple Health connection.
- User can create custom fitness achievements.
- Support 3 goal types:
  - One-shot achievement.
  - Tiered achievement.
  - Recurring + tiered goal.
- Automatically check Apple Health data for completion.
- Show current tier, progress, and next tier.
- Notify user when an achievement unlocks or levels up.

### MVP examples to support

- Run a 5K once.
- Run a 5K 1 / 5 / 10 / 25 / 50 times.
- Run a 5K under a target time.
- Walk X km per week, with lifetime tiers for repeated completions.

## Why the idea is interesting

The idea is not interesting because gamified fitness is new. Many apps already have badges, streaks, challenges, and RPG-style mechanics.

The interesting part is:

> User-created achievement chains that level themselves up using real-world data.

That makes it feel personal rather than generic. Instead of Apple, Strava, or Garmin deciding what counts as an achievement, the user defines what matters to them.

## Risks / questions

- Is automatic Apple Health detection accurate enough for custom rules?
- Can the achievement builder be simple without becoming confusing?
- Will users want to create their own goals, or do they need templates?
- How much gamification is motivating versus cheesy?
- Should the app be fitness-only at first, or include manual non-fitness goals from day one?
- How should tier progressions be chosen: user-defined, suggested templates, or both?

## Design principles

- Start with fitness.
- Make custom achievements the core mechanic.
- Avoid becoming a generic habit tracker too early.
- Keep the game layer lightweight.
- Make the unlock moment feel satisfying.
- Let completed goals naturally become the next challenge.
- Use templates so users do not have to design every achievement from scratch.

## Possible names / working titles

- Level Goals
- Real Life Achievements
- Achievement Engine
- Fitness Quests
- Life XP
- Next Tier
- Goalchain
- BadgeForge
- Personal Bests
- Unlock

## One-line summary

A fitness-first app where users create custom one-shot, recurring, and tiered achievements, then automatically unlock and level them up using real health data.
