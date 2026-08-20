"""
Central registry of modules shown in the ,help dropdown.
When you add a new cog, add an entry here so it shows up automatically.
"""

MODULES = {
    "Core": {
        "emoji": "🏠",
        "description": "Basic bot commands.",
        "commands": [
            ("ping", "Check the bot's latency."),
            ("help", "Show this help menu."),
        ],
    },
    "Information": {
        "emoji": "ℹ️",
        "description": "Look up info about the server, users, or the bot.",
        "commands": [
            ("serverinfo [si]", "Show stats about this server."),
            ("userinfo [ui, whois] [@user]", "Show stats about a user."),
            ("avatar [av, pfp] [@user]", "Show a user's avatar."),
            ("botinfo [bi, stats]", "Show stats about the bot."),
        ],
    },
    "Moderation": {
        "emoji": "🔨",
        "description": "Moderation tools. Requires the configured mod role.",
        "commands": [
            ("kick <@user> [reason]", "Kick a member."),
            ("ban <@user> [reason]", "Ban a member."),
            ("unban <user_id> [reason]", "Unban a user by ID."),
            ("timeout [mute] <@user> <minutes> [reason]", "Timeout a member."),
            ("untimeout [unmute] <@user> [reason]", "Remove a timeout."),
            ("warn <@user> [reason]", "Warn a member (saved permanently)."),
            ("warnings [warns] <@user>", "View a member's warnings."),
            ("clearwarnings [clearwarns] <@user>", "Clear a member's warnings."),
            ("purge [c, clear] <amount>", "Bulk delete recent messages."),
            ("slowmode <seconds>", "Set channel slowmode."),
        ],
    },
    "Config": {
        "emoji": "⚙️",
        "description": "Server configuration. Requires Administrator.",
        "commands": [
            ("setmodrole <@role>", "Set the role that counts as staff."),
            ("modrole", "Show the currently configured mod role."),
        ],
    },
    "AutoMod": {
        "emoji": "🛡️",
        "description": "Automatic spam/mention/word/link/caps filtering. Requires Administrator.",
        "commands": [
            ("automod", "Show current automod configuration."),
            ("automod toggle <on/off>", "Turn automod on or off entirely."),
            ("automod feature <spam/mentions/words/invites/caps> <on/off>", "Toggle a specific feature."),
            ("automod addword <word>", "Add a word to the banned words list."),
            ("automod removeword <word>", "Remove a word from the banned words list."),
            ("automod wordlist", "Show the banned words list."),
            ("automod logchannel [#channel]", "Set or clear the automod log channel."),
            ("automod ignorechannel <#channel>", "Toggle ignoring a channel."),
            ("automod spamsettings <limit> <seconds> <punishment> [minutes]", "Configure anti-spam."),
            ("automod mentionsettings <limit> <punishment> [minutes]", "Configure mass-mention detection."),
            ("automod capssettings <percent> [min_length]", "Configure excessive caps detection."),
        ],
    },
    "Lockdown": {
        "emoji": "🔒",
        "description": "Lock/hide channels. Requires the configured mod role.",
        "commands": [
            ("lock [#channel]", "Stop @everyone from sending messages in a channel."),
            ("unlock [#channel]", "Restore a channel's previous send permissions."),
            ("hide [#channel]", "Hide a channel from @everyone."),
            ("unhide [#channel]", "Restore a channel's previous visibility."),
            ("lockdown [lockall]", "Lock every text channel in the server."),
            ("unlockdown [unlockall]", "Unlock every text channel in the server."),
        ],
    },
    "Nuke": {
        "emoji": "💣",
        "description": "Clone-and-replace a channel to wipe its message history. Requires the configured mod role.",
        "commands": [
            ("nuke [#channel]", "Clone the channel (name, permissions, position, settings) and delete the original. Asks for confirmation first."),
        ],
    },
    "AutoResponder": {
        "emoji": "💬",
        "description": "Custom trigger → response messages. Requires the configured mod role to manage.",
        "commands": [
            ("autoresponder [ar]", "List all autoresponders for this server."),
            ("autoresponder add [ar add] <trigger> | <response>", "Add a new trigger. Placeholders: {user} {username} {server} {channel}"),
            ("autoresponder remove [ar remove] <trigger>", "Remove a trigger."),
            ("autoresponder clear [ar clear]", "Remove all triggers."),
            ("autoresponder toggle [ar toggle] <on/off>", "Enable or disable autoresponders."),
        ],
    },
    "Reaction Roles": {
        "emoji": "🎭",
        "description": "React to a message to get a role. Setup requires Administrator.",
        "commands": [
            ("reactionrole [rr]", "List all reaction role setups in this server."),
            ("reactionrole add [rr add] <message_id> <emoji> <@role>", "Link an emoji reaction to a role (run in the message's channel)."),
            ("reactionrole remove [rr remove] <message_id> <emoji>", "Unlink an emoji from a role."),
        ],
    },
    "Embed Builder": {
        "emoji": "🖼️",
        "description": "Build a custom embed with buttons and a live preview. Requires Manage Messages.",
        "commands": [
            ("embed [#channel]", "Open the interactive embed builder. Sends to the given channel, or the current one."),
        ],
    },
    "Snipe": {
        "emoji": "🔍",
        "description": "Recover recently deleted or edited messages in a channel. Not stored across restarts.",
        "commands": [
            ("snipe [s] [index]", "Show a recently deleted message (default: most recent)."),
            ("editsnipe [es] [index]", "Show a recently edited message, before and after."),
            ("clearsnipe [cs]", "Clear this channel's snipe history. Requires Manage Messages."),
        ],
    },
    "Logging": {
        "emoji": "📋",
        "description": "Log server events (joins, leaves, message edits/deletes, mod actions) to a channel. Requires Administrator.",
        "commands": [
            ("logs", "Show the current logging configuration."),
            ("logs setchannel [#channel]", "Set (or clear) the log channel."),
            ("logs toggle <event> <on/off>", "Toggle a specific event. Events: join, leave, kick, ban, unban, timeout, message_delete, message_edit, role_update, nickname_update"),
        ],
    },
    "Fun": {
        "emoji": "🎉",
        "description": "Fun and entertainment commands.",
        "commands": [
            ("8ball <question>", "Ask the magic 8-ball."),
            ("coinflip [flip, coin]", "Flip a coin."),
            ("roll [dice] <NdM>", "Roll dice, e.g. 2d20."),
            ("rps <rock/paper/scissors>", "Play rock-paper-scissors."),
            ("choose [pick] <a, b, c>", "Pick between options."),
            ("ship <@user1> [@user2]", "Ship two users together."),
            ("joke", "Get a random joke."),
            ("fact", "Get a random fun fact."),
            ("wyr [wouldyourather]", "Get a random 'would you rather'."),
            ("hug/pat/slap/kiss/cuddle [@user]", "Anime reaction gif interactions."),
            ("poke/tickle/punch/bite [@user]", "More reaction gif interactions."),
            ("highfive/wave/feed [@user]", "Even more reaction gif interactions."),
            ("fuck [@user]", "Not what you think — a comedic beatdown gif instead."),
        ],
    },
    "Economy": {
        "emoji": "💰",
        "description": "Earn, gamble, and compete with Aurels — the server's virtual currency.",
        "commands": [
            ("balance [bal, aurels] [@user]", "Check your (or someone's) balance."),
            ("daily", "Claim your daily reward (24h cooldown)."),
            ("jobs [joblist]", "See available jobs and their pay ranges."),
            ("apply <job>", "Apply for a job."),
            ("resign [quit]", "Quit your current job."),
            ("myjob [job]", "Show your current job."),
            ("work", "Work your job for Aurels (1h cooldown, requires a job)."),
            ("pay [give] <@user> <amount>", "Send Aurels to another member."),
            ("leaderboard [lb]", "Show the top 10 richest members."),
            ("cf <amount> <heads/tails>", "Bet on a coinflip."),
            ("slots <amount>", "Play the slot machine."),
        ],
    },
}
