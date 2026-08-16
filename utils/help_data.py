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
            ("clear [purge] <amount>", "Bulk delete recent messages."),
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
}
