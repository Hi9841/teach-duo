# Workspace files

The teaching workspace is the directory the user is learning in. It is not the skill directory. These files are the memory of the course. Keep each one short.

## MISSION.md

Why they are learning. One mission per workspace. Concrete, and shorter than a screen. Confirm before you change one that already exists.

```md
# Mission: {Topic}

## Why
{1-3 sentences. What changes when they have this skill?}

## Success looks like
- {A specific thing they will be able to do}

## Constraints
- {Time, prior commitments, how they want to practice}

## Out of scope
- {Adjacent topics they do not want right now}
```

## RESOURCES.md

Trusted sources. Lesson claims come from here. Annotate every entry in one line. Prune a source that turned out shallow. If they do not want a community, write that here.

```md
# {Topic} Resources

## Knowledge

- [Title by Author](https://example.com)
  What it covers, and when to reach for it.

## Wisdom (Communities)

- [Forum name](https://example.com)
  What it is good for.

## Gaps

- {Something the mission needs and no good source covers yet}
```

## learning-records/

`0001-slug.md`, numbered from the highest file that exists. Create the directory when you write the first record.

```md
# {What was learned or established}

{1-3 sentences: what is now known, and what that changes about the next lesson.}
```

Write one when they demonstrate a non-obvious idea, tell you they already know something and how deep that goes, correct a misconception, or shift the mission. Do not write one because a topic was covered. Do not duplicate a glossary line.

When a later record contradicts an earlier one, mark the old file `Status: superseded by LR-NNNN`. Do not delete it.

## GLOSSARY.md

Add a term only when they can use it. One or two sentences on what the term is. Pick one name and list the others under `_Avoid_`. Use the glossary's own terms inside later definitions. Revise a stale definition in place.

## NOTES.md

How they want to be taught. Not a second mission.
