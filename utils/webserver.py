"""
The bot's website — runs IN THE SAME PROCESS as the bot (see main.py), so
Wispbyte's subdomain has something to serve. Uses aiohttp, already installed
as a dependency of discord.py — no new packages needed.

Pages: home -> menu -> {commands, contact, privacy, terms}
The commands table is generated live from utils/help_data.py, so it can
never go out of sync with the bot's actual commands.
"""
import time

from aiohttp import web
from discord.ext import commands

from utils.help_data import MODULES

START_TIME = time.time()

# ---- Edit these for your bot ----
DEV_TAG = "@f.vyn"
CONTACT_URL = "https://discord.gg/vtcMwNwh23"  # your support server invite
# ----------------------------------

# Fallback favicon (a simple purple "E" icon), used only in the brief window
# before the bot finishes logging in. Once ready, the site uses the bot's
# real avatar as the favicon instead — no image file needed either way.
FALLBACK_FAVICON = (
    "data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='22' fill='%23222222'/>"
    "<text x='50' y='70' font-size='58' text-anchor='middle' "
    "fill='white' font-family='Arial,sans-serif' font-weight='bold'>E</text>"
    "</svg>"
)


BASE_STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }

    body {
        background: #000000;
        color: #f0f0f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        margin: 0;
        padding: 40px 16px;
        position: relative;
        overflow-x: hidden;
    }

    /* Animated ambient glow blobs — pure CSS, no images */
    body::before, body::after {
        content: "";
        position: fixed;
        width: 480px;
        height: 480px;
        border-radius: 50%;
        filter: blur(110px);
        opacity: 0.28;
        z-index: 0;
        animation: drift 16s ease-in-out infinite alternate;
    }
    body::before {
        background: #ffffff;
        top: -120px;
        left: -100px;
    }
    body::after {
        background: #808080;
        bottom: -140px;
        right: -100px;
        animation-delay: -8s;
    }
    @keyframes drift {
        0%   { transform: translate(0, 0) scale(1); }
        100% { transform: translate(40px, 30px) scale(1.15); }
    }

    /* Scattered starfield dots — pure CSS, no images */
    .stars {
        position: fixed;
        inset: 0;
        z-index: 0;
        background-image:
            radial-gradient(1.5px 1.5px at 20% 30%, rgba(255,255,255,0.35), transparent),
            radial-gradient(1.5px 1.5px at 70% 15%, rgba(255,255,255,0.25), transparent),
            radial-gradient(1px 1px at 40% 70%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 85% 60%, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 10% 85%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 60% 90%, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 90% 35%, rgba(255,255,255,0.25), transparent);
        background-repeat: no-repeat;
    }

    .card {
        position: relative;
        z-index: 1;
        background: rgba(20, 20, 20, 0.65);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 48px 44px;
        text-align: center;
        box-shadow:
            0 20px 60px rgba(0,0,0,0.5),
            0 0 0 1px rgba(255,255,255,0.02) inset,
            0 1px 0 rgba(255,255,255,0.06) inset;
        max-width: 560px;
        width: 100%;
        animation: rise 0.5s ease-out;
    }
    @keyframes rise {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .avatar-ring {
        width: 104px;
        height: 104px;
        border-radius: 50%;
        margin: 0 auto 20px;
        padding: 3px;
        background: linear-gradient(135deg, #ffffff, #808080, #1a1a1a);
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
    }
    img.avatar {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        display: block;
        border: 3px solid #0a0a0a;
    }

    h1 {
        margin: 0 0 6px;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff, #999999);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h2 { font-weight: 500; color: #a0a0a0; margin: 0 0 26px; font-size: 15px; }

    .meta {
        color: #b0b0b0;
        font-size: 13.5px;
        margin-bottom: 26px;
        line-height: 2;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 14px 18px;
    }
    .meta b { color: #ffffff; font-weight: 600; }

    .status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        color: #4ade80;
        font-weight: 600;
        margin-bottom: 20px;
        font-size: 13px;
        letter-spacing: 0.02em;
    }
    .status .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4ade80;
        box-shadow: 0 0 10px #4ade80;
        animation: pulse 1.8s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%      { opacity: 0.5; transform: scale(0.8); }
    }
    .status.offline { color: #f87171; }
    .status .dot.offline {
        background: #f87171;
        box-shadow: 0 0 10px #f87171;
    }

    .btn-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 6px;
    }

    a.btn, button.btn {
        display: block;
        background: linear-gradient(135deg, #ffffff, #d0d0d0, #a0a0a0);
        color: #0a0a0a;
        text-decoration: none;
        padding: 13px 20px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
        border: none;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
        box-shadow: 0 4px 16px rgba(255, 255, 255, 0.15);
    }
    a.btn:hover, button.btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(255, 255, 255, 0.25);
    }
    a.btn:active, button.btn:active { transform: translateY(0); }

    a.btn.secondary {
        background: rgba(255,255,255,0.05);
        color: #d5d5d5;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: none;
    }
    a.btn.secondary:hover {
        background: rgba(255,255,255,0.08);
        box-shadow: none;
    }

    .back-wrap { margin-top: 26px; }

    table { width: 100%; border-collapse: collapse; margin: 14px 0 6px; text-align: left; }
    th {
        color: #999999;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 8px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    td {
        padding: 10px 10px;
        font-size: 13.5px;
        color: #c9c9c9;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        vertical-align: top;
    }
    td.cmd {
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
        font-size: 13px;
    }
    .module-title {
        text-align: left;
        margin: 30px 0 4px;
        font-size: 14px;
        font-weight: 700;
        color: #f0f0f0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .content-text { text-align: left; font-size: 14px; line-height: 1.75; color: #b5b5b5; }
    .content-text h3 { color: #ffffff; font-size: 14.5px; font-weight: 700; margin: 24px 0 8px; }
    .content-text p { margin: 0 0 12px; }

    .wide-card { max-width: 720px; }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.25); border-radius: 8px; }
</style>
"""


def render_page(inner_html: str, wide: bool = False, favicon_url: str = FALLBACK_FAVICON) -> str:
    card_class = "card wide-card" if wide else "card"
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Elia</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="{favicon_url}">
    {BASE_STYLE}
</head>
<body>
    <div class="stars"></div>
    <div class="{card_class}">
        {inner_html}
    </div>
</body>
</html>
"""


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def build_app(bot: commands.Bot) -> web.Application:
    app = web.Application()
    total_commands = sum(len(m["commands"]) for m in MODULES.values())

    def favicon() -> str:
        if bot.user:
            return str(bot.user.display_avatar.url)
        return FALLBACK_FAVICON

    # ---------------- HOME ----------------
    async def home(request):
        if not bot.is_ready():
            inner = """
                <h1>Elia</h1>
                <div class="status offline"><span class="dot offline"></span>Offline</div>
            """
            return web.Response(text=render_page(inner, favicon_url=favicon()), content_type="text/html", status=503)

        dev_name = DEV_TAG
        inner = f"""
            <div class="avatar-ring">
                <img class="avatar" src="{bot.user.display_avatar.url}" alt="avatar">
            </div>
            <h1>{bot.user.name}</h1>
            <div class="status"><span class="dot"></span>Online</div>
            <div class="meta">
                dev: <b>{dev_name}</b><br>
                modules: <b>{len(MODULES)}</b> &nbsp;·&nbsp; commands: <b>{total_commands}</b><br>
                servers: <b>{len(bot.guilds)}</b>
            </div>
            <a class="btn" href="/menu">Next</a>
        """
        return web.Response(text=render_page(inner, favicon_url=favicon()), content_type="text/html")

    # ---------------- MENU ----------------
    async def menu(request):
        inner = """
            <h1>Elia</h1>
            <div class="btn-grid">
                <a class="btn" href="/help">Help</a>
                <a class="btn" href="/contact">Contact</a>
                <a class="btn" href="/privacy">Privacy</a>
                <a class="btn" href="/terms">Terms</a>
            </div>
            <div class="back-wrap"><a class="btn secondary" href="/">Back</a></div>
        """
        return web.Response(text=render_page(inner, favicon_url=favicon()), content_type="text/html")

    # ---------------- HELP ----------------
    async def help_page(request):
        inner = f"""
            <h1>Help</h1>
            <h2>Prefix: ,</h2>
            <a class="btn" href="/commands">Commands</a>
            <div class="back-wrap"><a class="btn secondary" href="/menu">Back</a></div>
        """
        return web.Response(text=render_page(inner, favicon_url=favicon()), content_type="text/html")

    # ---------------- COMMANDS (generated live from help_data.py) ----------------
    async def commands_page(request):
        sections = []
        for module_name, data in MODULES.items():
            rows = "".join(
                f"<tr><td class='cmd'>,{name.split(' ')[0]}</td><td>{desc}</td></tr>"
                for name, desc in data["commands"]
            )
            sections.append(f"""
                <div class="module-title">{data['emoji']} {module_name}</div>
                <table>
                    <tr><th>Command</th><th>Description</th></tr>
                    {rows}
                </table>
            """)

        inner = f"""
            <h1>Commands</h1>
            <h2>{total_commands} commands across {len(MODULES)} modules</h2>
            {"".join(sections)}
            <div class="back-wrap"><a class="btn secondary" href="/help">Back</a></div>
        """
        return web.Response(text=render_page(inner, wide=True, favicon_url=favicon()), content_type="text/html")

    # ---------------- CONTACT ----------------
    async def contact(request):
        inner = f"""
            <h1>Contact Us</h1>
            <div class="meta">Questions, bug reports, or feedback? Reach out on our Discord.</div>
            <a class="btn" href="{CONTACT_URL}" target="_blank">Join Support Server</a>
            <div class="back-wrap"><a class="btn secondary" href="/menu">Back</a></div>
        """
        return web.Response(text=render_page(inner, favicon_url=favicon()), content_type="text/html")

    # ---------------- PRIVACY ----------------
    async def privacy(request):
        inner = """
            <h1>Privacy Policy</h1>
            <div class="content-text">
                <p>Last updated: today. This policy explains what data Elia ("the Bot", "we", "us") collects and how it's used.</p>

                <h3>1. Data We Collect</h3>
                <p>Elia stores only what's needed for its features to work, scoped per server:</p>
                <p>
                    • Moderation warnings: warned user's ID, moderator's ID, reason, server ID, and timestamp.<br>
                    • Server configuration: mod role, automod settings, banned word lists, log channel, autoresponder triggers/responses, reaction role mappings.<br>
                    • Economy data: your balance, job, and cooldown timestamps, scoped to each server.<br>
                    • Recently deleted/edited messages ("snipe") are kept in memory only, never written to disk, and expire automatically.
                </p>
                <p>No message content is stored long-term outside of what's listed above. We do not log or store your DMs.</p>

                <h3>2. Third-Party Services</h3>
                <p>Some fun commands (reaction gifs) fetch content from a third-party GIF provider at the time you run them. No personal data is sent to these providers beyond what's needed to make the request.</p>

                <h3>3. How We Use Data</h3>
                <p>Stored data is used solely to power the Bot's features — for example, so moderators can view a member's warning history, or so your economy balance persists. We do not sell, rent, or share this data, and we do not use it for advertising or profiling.</p>

                <h3>4. Data Retention & Deletion</h3>
                <p>Data is retained for as long as Elia remains in the relevant server, or until removed by a server admin using the Bot's own commands. If you'd like your data removed, contact us — see the Contact page.</p>
            </div>
            <div class="back-wrap"><a class="btn secondary" href="/menu">Back</a></div>
        """
        return web.Response(text=render_page(inner, wide=True, favicon_url=favicon()), content_type="text/html")

    # ---------------- TERMS ----------------
    async def terms(request):
        inner = """
            <h1>Terms of Service</h1>
            <div class="content-text">
                <p>Last updated: today. These Terms govern your use of the Discord bot Elia ("the Bot", "we", "us"). By adding Elia to a Discord server or otherwise interacting with it, you agree to these Terms.</p>

                <h3>1. Use of the Bot</h3>
                <p>Elia is provided for use within Discord servers in accordance with Discord's Terms of Service and Community Guidelines. You may not use Elia to violate Discord's rules, applicable law, or the rules of any server in which the Bot operates.</p>

                <h3>2. Moderation Features</h3>
                <p>Elia includes moderation tooling, including the ability for server administrators and moderators to issue and track warnings against members. Server staff are responsible for using these features appropriately and in accordance with their own server rules.</p>

                <h3>3. Third-Party Services</h3>
                <p>Elia integrates with third-party GIF providers to power certain fun commands. Use of these features means content is requested from those third-party services. We are not responsible for the content, availability, or practices of these external services.</p>

                <h3>4. Availability</h3>
                <p>Elia is provided "as is" without warranties of any kind. We do not guarantee uninterrupted or error-free operation and may modify, suspend, or discontinue the Bot, in whole or in part, at any time without notice.</p>

                <h3>5. Limitation of Liability</h3>
                <p>To the maximum extent permitted by law, we are not liable for any indirect, incidental, or consequential damages arising from your use of, or inability to use, Elia.</p>

                <h3>6. Termination</h3>
                <p>We reserve the right to restrict or terminate access to Elia for any server or user that violates these Terms, Discord's Terms of Service, or Discord's Community Guidelines.</p>

                <h3>7. Changes to These Terms</h3>
                <p>We may update these Terms from time to time. Continued use of Elia after changes are posted constitutes acceptance of the revised Terms.</p>

                <h3>8. Contact</h3>
                <p>Questions about these Terms can be directed to us — see the Contact page.</p>
            </div>
            <div class="back-wrap"><a class="btn secondary" href="/menu">Back</a></div>
        """
        return web.Response(text=render_page(inner, wide=True, favicon_url=favicon()), content_type="text/html")

    async def health(request):
        return web.json_response({"status": "ok", "ready": bot.is_ready()})

    app.router.add_get("/", home)
    app.router.add_get("/menu", menu)
    app.router.add_get("/help", help_page)
    app.router.add_get("/commands", commands_page)
    app.router.add_get("/contact", contact)
    app.router.add_get("/privacy", privacy)
    app.router.add_get("/terms", terms)
    app.router.add_get("/health", health)
    return app


async def start_webserver(bot: commands.Bot, host: str, port: int):
    """Starts the web server as a background task. Non-blocking — call this before bot.start()."""
    app = build_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    return runner
