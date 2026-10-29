# bank job: plan

a ~22 s vertical (9:16) pixel-art diorama short of a bank robbery with a twist,
built with the diorama playbook (https://github.com/sloemo01/diorama, MIT,
read-only clone at /home/user/sloemo01/diorama, commit 37739e8). scribbleplot is
just the repo to code in; nothing here depends on the processing sketches.

## story (beats, seconds)

| t | beat | picture | sound |
| --- | --- | --- | --- |
| 0–2 | hook | close on the bank door, windows flash red | alarm bell starts hard, no lead-in |
| 2–8 | the run | robbers burst out with bright money bags, pile into the getaway sedan | door bang, running footsteps, car doors |
| 8–13 | the twist | the sedan will not start | engine sputter x3, sirens rising far off |
| 13–19 | caught | two cruisers screech in, red/blue wash over the slab, hands up, one bag spills cash | tire screech, siren close, coins/cash spill, sting |
| 19–22 | reset | pull back wide, street empties to the opening frame | ambience only, seamless loop back to 0 |

overlay text for the post (added in the edit, not in the scene): "the getaway
driver had one job".

## pipeline

1. scene: copy the needed modules from the diorama `templates/` into
   `bank-job/src/` (keep the MIT notice), fill `DESIGN.md`, build the street
   slab, bank, sedan, two cruisers, four robbers, four officers. everything a
   pure function of `t`, with `window.__diorama.freeze(t)`.
2. render: headless chromium (playwright is preinstalled) steps `freeze(t)` at
   30 fps and screenshots each frame; ffmpeg encodes. render the square scene
   large, then cut a 1080x1920 version with punch-ins (wide, door, car, wide).
3. sound: elevenlabs sound effects, cued from the beat table above, mixed with
   ffmpeg. deliver one mp4 with sfx and one without audio.
4. qa: the diorama `templates/qa/` scripts (shoot, frames, strip) before
   anything is shown.

## sound effects to generate (elevenlabs /v1/sound-generation)

| id | prompt | seconds |
| --- | --- | --- |
| alarm | old brass bank alarm bell ringing loudly, metallic clanging, urgent | 4 (loop) |
| door | heavy glass bank door slammed open | 1 |
| run | several people running on pavement, sneakers, panicked | 3 |
| cardoors | three car doors slamming in quick succession | 1.5 |
| sputter | old sedan engine cranking and failing to start, sputtering, three tries | 4 |
| sirens | police sirens approaching from a distance, doppler | 6 |
| screech | car tires screeching to a sudden stop on asphalt | 1.5 |
| cash | bag dropped, coins and bills spilling on pavement | 1.5 |
| sting | short comedic cartoon fail sting, trombone wah wah | 2 |
| street | quiet daytime city street ambience, distant traffic, birds | 10 (loop) |

## environment notes

- the elevenlabs account is connected through composio, but composio's
  `proxy_execute` drops binary responses: a sound-generation test call ran (and
  used credits) but returned an empty body. do not retry it that way.
- api.elevenlabs.io is blocked by this environment's network policy. the fix is
  to allow that domain in the environment's network settings and add the api key
  as a network secret / env var `ELEVENLABS_API_KEY`, then start a new session.
- npm works (three, esbuild, playwright-core install fine). kenney.nl and
  freesound.org are blocked.
