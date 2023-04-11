# Morning Workout bot
[t.me/MorningWorkoutBot](https://t.me/MorningWorkoutBot)
  
This is a Telegram bot that generates random exercises for different major muscle groups (upper, middle or lower body). Sometimes, the bot may trigger special events:
- 5% probability of a "Chill" event – means you may skip your workout today
- 10% probability of a "Double" event – means you should do twice as many reps for each exercise this time.  

The process of special events is sampled from Pseudo Random Distribution (like random-based abilities in Dota 2). For more information on how this works, check out this link: [github.com/supawesome/PRD](https://github.com/supawesome/PRD)


## Usage
- Start a conversation with the bot by searching for it in Telegram: [t.me/MorningWorkoutBot](https://t.me/MorningWorkoutBot)
- Type /start to start the bot
- Tap on the dice to get a set of random exercises  
Each exercise belongs to a different major muscle group (upper, middle or lower body)
- Follow the instructions provided in the Telegram bot for each exercise.

## Deployment
This bot is deployed on Fly.io and uses a Supabase Postrgres database.

\
\
\
\
\
TODO:
- [x] finalize texts
- [x] add GIFs/videos of exercises
- [ ] ~~add Shrek-related version~~