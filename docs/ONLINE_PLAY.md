# Online play: system design

Status: proposal, October 2026. It builds on the web app in `web/` (PR #8): the rules, the game session
and the screens already run in TypeScript, on the web and on phones.

The goal is to let two people in different places play each other: first friends through an invite link,
then strangers through matchmaking. Games against the computer stay on the device and need nothing below.

## 1. Requirements

### Functional

Phase 2, friends online:

- Invite a friend with a link and play on the web or in the phone apps.
- Start without signing up: a guest account with a display name.
- The server rolls the dice and checks every turn, so nobody can pick their dice or make an illegal move.
- Both players see a turn within a second of it ending.
- Reconnect after a dropped connection or after closing the app, and continue where the game was.
- A game with an absent player ends: when the turn clock runs out, the other player wins.
- Resign. Every game is kept with all its turns.

Phase 3, strangers:

- "Play online" pairs players of similar strength.
- Ratings and a leaderboard; accounts that work across devices (email, Google, Apple).
- Report and block players.

Not in scope yet: the doubling cube and matches to several points, chat, tournaments, spectators.

### Non-functional

- **Latency:** a committed turn reaches the opponent in under 1 s at p95, worldwide. The game is turn based,
  so 200 to 300 ms of network time is fine.
- **Correctness:** the server is the only authority on dice and positions. A client never decides an outcome.
- **Availability:** 99.5% is enough at launch. An outage may pause games but must never corrupt or lose one.
- **Cost:** tens of dollars a month at launch, growing roughly in line with the number of games.
- **Privacy:** data hosted in the EU, as little personal data as possible, account deletion in the app.

### Constraints

- One developer working with Claude. The app is TypeScript, and its rules are checked against the Python code.
- Existing accounts: a Supabase organization on the Pro plan with 8 projects, all in eu-central-1 (Frankfurt),
  and Vercel teams including a Pro team.
- The phone apps are the same web build wrapped with Capacitor.

### Assumptions to check after launch

- Launch: about 1,000 daily players, 3 online games each a day, 10% of them online at the busiest time.
- A game has about 50 turns and lasts about 12 minutes.
- This design should carry the game up to about 20,000 daily players before the game path needs to change.

## 2. High-level design

```
  Players: browser, iPhone app, Android app (the same web build)
     |                        |                              |
     | static files           | actions (HTTPS)              | updates (WebSocket)
     v                        v                              v
 +-----------+   +--------------------------------------------------------------------+
 | Vercel    |   | Supabase project "backgammon", eu-central-1                        |
 | web app,  |   |                                                                    |
 | invite    |   |  Auth: guests (anonymous sign-in), later email, Google, Apple      |
 | links     |   |                                                                    |
 +-----------+   |  Edge Function "play" (Deno, TypeScript)                           |
                 |    imports the same rules and game session as the app              |
                 |    create, join, turn, resign, claim, queue                        |
                 |         |  validates the turn, rolls the dice, then one transaction|
                 |         v                                                          |
                 |  Postgres: profiles, games, game_turns, match_queue                |
                 |         |  trigger on games: realtime.send(...)                    |
                 |         v                                                          |
                 |  Realtime: private channel game:<id>  (new state, presence)        |
                 |            private channel user:<id>  (match found)                |
                 |                                                                    |
                 |  pg_cron: every minute, ends games whose turn clock ran out        |
                 +--------------------------------------------------------------------+
```

Four principles carry the design:

1. **One write path.** Every change to a game goes through the Edge Function and a single Postgres
   transaction. Players can read their own games but cannot write them.
2. **One rules implementation.** The function imports `web/src/game/rules.ts` and `session.ts`, the same code
   the app runs and the parity tests check against the Python rules. The server and the client can never
   disagree about what is legal.
3. **A whole turn per request.** The player moves and undoes on their own device exactly as today, with no
   network involved. Done sends all the steps of the turn at once. The server replays them through
   `GameSession`; it accepts the turn only if every step is legal and no die that could be played is left,
   which is the same check that enables Done in the app today.
4. **The database announces every change.** A trigger on `games` broadcasts the new state, so nothing can be
   committed without being sent. A client that missed a message reads the row again.

### One turn, end to end

```
 White's app             Edge Function "play"            Postgres                   Black's app
     |  moves and undoes locally, no network
     |-- POST /turn {game, version 41, steps} -->|
     |                   | read the game: version 41, dice 6 and 4, White to move
     |                   | replay the steps with GameSession: each legal, every playable die used
     |                   | roll Black's dice with crypto.getRandomValues
     |                   |-- rpc commit_turn(game, 41, new state, turn) -->|
     |                   |                          | UPDATE games ... WHERE version = 41
     |                   |                          | INSERT INTO game_turns ...
     |                   |                          | trigger: realtime.send to game:<id>
     |<-- 200 {version 42, state} ---------------|                          |--- state 42 ---->|
     |                                                                     slides White's steps,
     |                                                                     shows Black's dice
```

Expected time from Done to the opponent's screen: 150 to 400 ms. The turn itself is about 1 KB.

## 3. Deep dive

### 3.1 Data model

```sql
create table profiles (
  id uuid primary key references auth.users on delete cascade,
  display_name text not null check (char_length(display_name) between 2 and 20),
  rating int not null default 1500,
  rated_games int not null default 0,
  created_at timestamptz not null default now()
);

create type game_status as enum ('waiting', 'active', 'finished', 'aborted');
create type game_end as enum ('borne_off', 'resigned', 'timeout', 'abandoned');

create table games (
  id uuid primary key default gen_random_uuid(),
  mode text not null check (mode in ('friend', 'casual', 'ranked')),
  status game_status not null default 'waiting',
  white_id uuid references profiles,
  black_id uuid references profiles,
  invite_code text unique,            -- friend games: short, random, unguessable
  state jsonb not null,               -- what GameSession needs: board, player, dice, dice left, opening, turns, hits
  version int not null default 0,     -- +1 on every change, for compare-and-set writes
  turn_player smallint,               -- 1 white, -1 black, null when the game is not active
  turn_deadline timestamptz,
  clocks jsonb,                       -- reserve time left per player
  winner smallint,
  ended_by game_end,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index games_active_deadline on games (turn_deadline) where status = 'active';
create index games_white on games (white_id);
create index games_black on games (black_id);

create table game_turns (
  game_id uuid references games on delete cascade,
  ply int,                            -- 1, 2, 3 ...
  player smallint not null,
  dice smallint[] not null,
  steps jsonb not null,               -- [[position, jump], ...] in the order the session takes them
  created_at timestamptz not null default now(),
  primary key (game_id, ply)
);

-- Phase 3
create table match_queue (
  user_id uuid primary key references profiles on delete cascade,
  mode text not null,
  rating int not null,
  joined_at timestamptz not null default now()
);
```

Row level security:

- `profiles`: any signed-in user reads display names and ratings; each user updates only their own display name.
- `games` and `game_turns`: readable by the two players of the game. There are no insert, update or delete
  policies; only the Edge Function writes, with the secret key.
- `realtime.messages`: a user may join `game:<id>` only as a player of that game, and `user:<id>` only as that user.

`GameSession` gets `snapshot()` and `restore(snapshot)`, so the app and the server both start a session from the
stored state.

### 3.2 API

A single Edge Function, `play`, with a small router: one function stays warm instead of six that start cold.

| Call | Body | Answer | Errors |
| --- | --- | --- | --- |
| `POST /play/games` | `{color}` | `{game_id, invite_url}` | |
| `POST /play/games/join` | `{invite_code}` | `{game_id}`; the server makes the opening roll and the game starts | 404 unknown code, 409 already started, 403 own game |
| `POST /play/games/:id/turn` | `{version, steps}` | `{version, state}` | 409 stale (with the current state), 422 illegal turn, 403 not your turn |
| `POST /play/games/:id/resign` | `{version}` | `{version, state}` | 409 stale |
| `POST /play/games/:id/claim` | `{}` | `{state}` when the opponent's clock ran out | 409 the clock has not run out |
| `POST /play/queue` | `{mode}` | `{status: 'queued'}` or `{status: 'matched', game_id}` (phase 3) | |
| `DELETE /play/queue` | | | |

Reads need no function: the app reads its games, their turns and profiles with supabase-js under row level security.

Realtime events:

- `game:<id>`, private: `state` with `{version, state, last_turn: {player, dice, steps}}`, sent by the trigger.
  Presence keyed by user id shows whether the opponent is in the game.
- `user:<id>`, private: `matched` with `{game_id}`.

The app uses the new publishable key; the secret key lives only in the function. The legacy `anon` and
`service_role` keys stop working at the end of 2026.

### 3.3 Dice and fairness

- Dice come from `crypto.getRandomValues` with rejection sampling (bytes 0 to 251, modulo 6), so no face is more likely.
- The opening roll happens on join; ties are rolled again on the server.
- **The next roll happens at commit.** When a turn is committed, the server rolls the next player's dice in the
  same transaction. That saves one request per turn, and seeing the dice early gives no advantage because there is
  no doubling cube to decide on. Roll dice stays in the app and reveals the dice already rolled. When the cube
  arrives, rolling becomes its own action after the cube decision.
- Every turn is stored with its dice and steps in `game_turns`: a complete record for disputes, replays and
  checking the dice distribution.

### 3.4 Changes in the app

- An `OnlineController`, the counterpart of `AIController`: it subscribes to `game:<id>`, plays the opponent's
  steps one by one with the same pace and slides, and sends the local player's turn when they press Done.
  `GameModel` stays as it is: the opponent is driven by a controller, the computer or the network.
- While a turn is being sent, the board shows the new position and the controls wait. A 409 resyncs to the
  server's state. A 422 resyncs and says the turn was not accepted, which an honest app never sees.
- On returning to the app or rejoining the channel, the app reads the game row. One version behind: it slides the
  missed turn. Further behind: it shows the current position.
- Invite links look like `https://<domain>/join/<code>`. They open the installed app through universal links
  (iOS) and app links (Android), otherwise the web app. Either one signs in as a guest when needed and joins.

### 3.5 Clocks and abandoned games

- Live games: 60 seconds per turn plus a 3 minute reserve per player, like a chess clock, so a long think now
  and then costs nothing. The server writes `turn_deadline` with every commit.
- Two ways the clock is enforced: the waiting player's app calls `claim` the moment the deadline passes, and a
  `pg_cron` job ends expired games every minute, for when both players are gone.
- An invite nobody opens expires after 7 days.
- Presence shows "Opponent is away" when the other player leaves the app; their clock keeps running.

### 3.6 Matchmaking and ratings (phase 3)

- `queue` looks for the longest waiting player within a rating window that grows the longer a player waits
  (start at 100 points, add 50 every 10 seconds). It runs `select ... for update skip locked` inside one
  transaction, so two searches can never take the same opponent. Without a match the player is queued and the
  app asks again every 5 seconds. A match creates the game, removes both players from the queue, and sends
  `matched` on both user channels.
- Ratings use the FIBS formula for 1 point matches, the usual system on backgammon servers. They update in the
  same transaction that finishes the game. Only permanent accounts play ranked, so farming rating with throwaway
  guest accounts is harder.
- While few players are online, the waiting screen offers a game against the computer.

### 3.7 Errors and retries

- **A turn request fails on the network:** the app sends it again with the same version. A duplicate is answered
  409 with a state that already contains the turn, and the app recognizes its own turn there.
- **The function fails:** the app retries 3 times after 0.5, 1 and 2 seconds. After that it shows "Connection
  lost, retrying" and keeps trying while the game is open. The clock runs on the server, so this cannot go on forever.
- **Realtime drops:** supabase-js reconnects, and every rejoin reads the row again, because missed broadcasts are
  not replayed.
- **Two writes race:** each write is a compare-and-set on `version`, so the second one gets a 409.

### 3.8 Security and abuse

- Server authority as described: clients have no write access to games.
- Guest sign-in is protected with a CAPTCHA (Cloudflare Turnstile) against mass account creation, on top of
  Supabase's sign-in rate limits.
- Display names: 2 to 20 characters, filtered for offensive words, and reportable. No free text chat at launch.
- At most about 30 actions per minute per user in the function.
- iOS requires a privacy-focused login option, such as Sign in with Apple, when Google sign-in is offered.
- The App Store and Google Play both require account deletion inside the app.

### 3.9 Privacy

- Personal data: display name, optional email, and games, all stored in Frankfurt.
- Deleting an account deletes the profile and keeps the games with the player shown as "Deleted player".
- A privacy policy and terms of use go live before the first public online game.

## 4. Scale and reliability

### Load estimate

One online game: about 50 turn commits, so 50 function calls, 100 database writes and about 150 Realtime
messages (each turn is 1 message sent and 2 delivered), plus presence.

| | Launch, 1,000 daily players | Growth, 20,000 daily players |
| --- | --- | --- |
| Online games a day | 1,500 | 30,000 |
| Function calls a month | 2.3 million | 45 million |
| Realtime messages a month | about 7 million | about 135 million |
| Players connected at the busiest time | about 100 | about 2,000 |
| Turns a second at the busiest time | under 5 | about 60 |

Cost on top of the Supabase Pro plan you already pay, from Supabase's published prices in October 2026
(check them again before deciding):

- **Launch, about $20 a month:** compute for the new project about $10, function calls over the 2 million
  included $2, Realtime messages over the 5 million included about $5.
- **Growth, about $450 a month:** function calls about $86, Realtime messages about $330, connections over the
  500 included $15, a larger database instance $15 to $60.

Realtime messages are the largest cost as the game grows.

Pro limits to remember: with the spend cap on, Realtime allows 500 connections and 500 messages a second.
Turning the cap off raises that to 10,000 connections and 2,500 messages a second. Turn it off before about
300 players are online at once.

### Scaling

- The Edge Function holds no state, so Supabase runs as many copies as needed.
- Postgres rows are small; 60 writes a second at the growth size is light work for a Small or Medium instance.
  The partial index keeps the clock check fast.
- Realtime stays within the Pro limits up to 10,000 connections with the spend cap off.
- The static app is served from Vercel's CDN.

### Failure and recovery

- Supabase runs in one region with daily backups on Pro; point in time recovery can be added.
- Every game lives in Postgres, so a failure of the function or of Realtime never loses a game.
- After an outage, an admin function moves all deadlines later by the length of the outage, so nobody loses on time.

### Monitoring and alerts

- Supabase function logs and reports. Alert when more than 1% of turn requests fail or their p95 passes 1 second.
- Sentry in the app and in the function for errors and stack traces, by release.
- PostHog, which is already connected, for the invite funnel: invite created, opened, game started, game finished.
- A canary: a scheduled job every 15 minutes plays a short game between two bots through the real API and
  alerts when it fails.
- Counters for games started, finished and abandoned, and for 422 illegal turns, which should stay near zero.
  A jump means an app bug or tampering.

## 5. Trade-offs

### Where the game authority runs

| | A. Supabase Edge Function, Postgres and Realtime (proposed) | B. A Cloudflare Durable Object per game, Supabase for accounts and history | C. A Node WebSocket server, for example Colyseus on Fly.io |
| --- | --- | --- | --- |
| Time to the first online game | Shortest: the accounts exist and it is one platform | Medium: a second platform, and sign-in bridged between them | Longest: servers to run and scale |
| Reuses the TypeScript rules | Yes | Yes | Yes |
| Time for a turn to arrive | 150 to 400 ms | 50 to 150 ms, the game is in memory | 50 to 150 ms |
| Operations | None | Little | Deploys, scaling and uptime are yours |
| Cost at launch | About $20 a month | Low | Low, but servers run around the clock |
| Cost at scale | Realtime messages dominate | Lowest per game | Depends on the servers |
| Live extras: watching moves as they happen, spectators | Possible with broadcast, less natural | Natural | Natural |

**Choose A now.** A turn-based game does not need 100 ms latency, and A has the fewest moving parts for one
developer. Move to B when Realtime costs or latency become the problem: the rules, the API and the app's
controller carry over, only the server side of the game changes.

### Other decisions

| Decision | Chosen | Instead of | Why, and the cost |
| --- | --- | --- | --- |
| What a request carries | A whole turn | Each step | One request per turn, undo stays local and instant, and the check is the existing Done rule. Cost: the opponent sees the steps only after Done. A later option is broadcasting the steps as an unconfirmed preview. |
| When the dice roll | At the previous commit | A separate Roll request | One request per turn instead of two. Has to change when the doubling cube arrives. |
| How updates reach players | A trigger that broadcasts on a private channel | Postgres Changes | Broadcast is what Supabase recommends at scale; Postgres Changes checks row level security for every subscriber on every change. |
| First sign-in | Guest | Sign-up form | An invite link plays in one tap. Cost: a guest who clears the browser loses their history, so the app offers to save the account after a few games. |
| Where the data lives | A new Supabase project | Inside an existing project | Separate data, keys and limits, for about $10 a month of compute. |

## 6. Phases

1. **2a, friends online on the web:** the schema and row level security, the `play` function (create, join, turn,
   resign, claim), guest sign-in, invite links, `OnlineController`, presence, clocks and the `pg_cron` job.
   Tests: function tests for illegal, stale and out of turn requests; an end to end test with two browsers
   playing each other against a local Supabase stack in CI.
2. **2b, the phone apps:** Capacitor builds, universal links and app links for invites, push notifications for
   "your turn" and invites (a device tokens table and a sending function).
3. **2c, games at your own pace:** a day per turn, built on the push notifications.
4. **3, strangers:** permanent accounts, ratings, matchmaking, leaderboard, report and block.

To check early in 2a: that the Supabase bundler accepts imports of `web/src/game` from the function. If it does
not, the shared game code moves to `supabase/functions/_shared/game` and the app imports it from there through a
Vite alias.

## 7. What to revisit as the game grows

- **About 300 players online at once:** turn off the Supabase spend cap, or the 500 connection limit starts
  turning players away.
- **About 5,000 at once, or a Realtime bill over about $300 a month:** move live game rooms to Durable Objects
  (option B) and keep Supabase for accounts, profiles and history.
- **Players in the Americas or Asia say turns feel slow:** measure p95 by country first; add a second region
  only if the numbers call for it.
- **Matchmaking waits grow, or searches contend for the same rows:** a separate matcher process, and computer
  opponents as fill-ins, clearly labeled as such.
- **Ranked play gets serious:** compare players' moves with the network's choices to flag engine use.
- **Doubling cube and longer matches:** a separate roll action, cube actions, and match scores in the state.

## 8. Open questions

1. Live games with a clock only at first, or also games at your own pace with notifications?
2. Frankfurt as the region, like your other projects?
3. A new Supabase project named "backgammon" in your Pro organization, at about $10 a month?
4. Is 60 seconds per turn plus a 3 minute reserve right for live games?
