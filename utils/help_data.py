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
            ("hug/pat/slap [@user]", "Interact with someone."),
        ],
    },
}
