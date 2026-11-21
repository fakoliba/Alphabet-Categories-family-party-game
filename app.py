"""Run Alphabet Categories locally using only Python's standard library."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
import webbrowser

from alphabet_categories.game import DEFAULT_CATEGORIES, draw_letter, new_game, scoreboard, submit_answer, winners
from alphabet_categories.storage import load_data, save_data

HOST, PORT = "127.0.0.1", 8765
DATA = load_data()

STYLE = """
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#28221c;background:#fff9ed}*{box-sizing:border-box}
body{margin:0;padding:24px;background:radial-gradient(circle at top right,#ffe7a8,transparent 35%),#fff9ed;min-height:100vh}
main{max-width:880px;margin:auto}.card{background:#fff;border:2px solid #f0dfbf;border-radius:24px;padding:24px;margin:18px 0;box-shadow:0 8px 24px #5f431014}
h1{font-size:clamp(2.2rem,8vw,4rem);margin:.1em 0;color:#713e20}h2{margin-top:0}.muted{color:#766b5f}.row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
label{display:block;font-weight:700;margin:10px 0 5px}input,select,button{font:inherit;padding:11px 13px;border:2px solid #e7d7ba;border-radius:12px;background:white}
input[type=text]{min-width:150px;max-width:100%}input[type=color]{height:48px;width:62px;padding:4px}input[type=checkbox]{width:20px;height:20px;vertical-align:middle}
button{cursor:pointer;background:#f9b844;border-color:#f2a82a;font-weight:800;color:#472c13}button.secondary{background:#fff;border-color:#d8c5a5}button.good{background:#7fc98e;border-color:#62b875}button.bad{background:#ffaaa0;border-color:#ee8d82}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(54px,1fr));gap:8px}.tile{font-size:1.2rem;font-weight:900;text-align:center;padding:10px 4px;background:#ffe3a2;border:2px solid #eeb85c;border-radius:12px;box-shadow:0 3px #cf9941}.used{opacity:.3;filter:grayscale(1)}
.letter{font-size:clamp(6rem,24vw,12rem);line-height:1;color:#dc6b34;text-align:center;font-weight:1000;text-shadow:0 5px #f3c08a}.pill{display:inline-block;background:#fff1cd;border-radius:99px;padding:6px 12px;margin:3px}.player{display:flex;align-items:center;gap:10px;padding:10px;border-bottom:1px solid #eee}.swatch{width:18px;height:18px;border-radius:50%}.winner{text-align:center;font-size:1.4rem}
@media(max-width:560px){body{padding:12px}.card{padding:17px}.row>*{flex:1 1 100%}input[type=color]{flex:0 0 62px}}
</style>
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(content: str) -> bytes:
    body = f"<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Alphabet Categories</title>{STYLE}<body><main><h1>🔤 Alphabet Categories</h1><p class='muted'>A cozy, offline word game for the whole table.</p>{content}<p class='muted'>Runs on this device only · No accounts or internet required</p></main></body></html>"
    return body.encode()


def render() -> bytes:
    game = DATA.get("active_game")
    if not game:
        settings = DATA.get("settings") or {}
        players = settings.get("players", [{"name": "Player 1", "color": "#f97316"}, {"name": "Player 2", "color": "#3b82f6"}])
        cats = settings.get("categories", list(DEFAULT_CATEGORIES))
        player_fields = "".join(f"<div class='row'><div><label>Player {i+1}</label><input name='player_name' value='{esc(p['name'])}' required></div><div><label>Color</label><input type='color' name='player_color' value='{esc(p['color'])}'></div></div>" for i,p in enumerate(players))
        category_text = ", ".join(cats)
        content = f"""<section class='card'><h2>Set up your table</h2><form method='post'><input type='hidden' name='action' value='start'>
        <label>Players (up to 8)</label>{player_fields}<button class='secondary' name='action' value='add_player'>＋ Add a player</button>
        <label>Categories (comma separated)</label><input style='width:100%' name='categories' value='{esc(category_text)}'>
        <div class='row'><div><label>Timer</label><select name='timer'><option value='30'>30 seconds</option><option value='60' selected>60 seconds</option><option value='90'>90 seconds</option><option value='0'>Off</option></select></div>
        <div><label>Rounds (blank = letters run out)</label><input name='round_limit' type='number' min='1' placeholder='Off'></div></div>
        <p><label><input type='checkbox' name='hard'> Skip Q, X and Z</label><label><input type='checkbox' name='spin'> Spin categories randomly</label></p>
        <button type='submit'>Start game</button></form></section>"""
        return page(content)

    board = "".join(f"<span class='tile {'used' if c in game['used_letters'] else ''}'>{c}</span>" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    rows = "".join(f"<div class='player'><span class='swatch' style='background:{esc(p['color'])}'></span><strong>{esc(p['name'])}</strong><span>{p['score']} pts</span></div>" for p in scoreboard(game))
    history = "".join(f"<p><b>{esc(t['player_name'])}</b> · {esc(t['letter'])} / {esc(t['category'])}: {esc(t['answer'] or 'No answer')} — {'👍' if t['accepted'] else '👎'}</p>" for t in reversed(game['history'][-12:]))
    if game['status'] == 'complete':
        win = winners(game)
        wintext = " & ".join(esc(p['name']) for p in win)
        content = f"<section class='card winner'><h2>🎉 Game complete!</h2><p>Winner: <b>{wintext}</b></p><form method='post'><button name='action' value='new'>Play again</button></form></section>"
    elif game['pending_turn']:
        t = game['pending_turn']; player = next(p for p in game['settings']['players'] if p['id']==t['player_id'])
        elapsed = max(0, int(__import__('time').time()-t['started_at']))
        limit = game['settings']['timer_seconds']; remaining = max(0, limit-elapsed) if limit else None
        clock = f"<span class='pill'>⏱ {remaining}s</span>" if remaining is not None else "<span class='pill'>Timer off</span>"
        content = f"""<section class='card'><p>Turn {t['turn_number']} · Round {t['round_number']} {clock}</p><h2>{esc(player['name'])}, your turn!</h2><div class='letter'>{esc(t['letter'])}</div><h2>Say a {esc(t['category'])} starting with {esc(t['letter'])}</h2>
        <form method='post'><label>Optional answer record</label><input style='width:100%' name='answer' value='{esc(t.get('answer_draft',''))}'><p>Everyone votes at the table:</p><button class='good' name='action' value='accept'>👍 Accept · Score 1</button> <button class='bad' name='action' value='reject'>👎 Reject · Score 0</button> <button class='secondary' name='action' value='refresh'>Refresh timer</button></form></section>"""
    else:
        content = f"<section class='card'><h2>Letter board</h2><div class='tiles'>{board}</div><p>{len(game['used_letters'])} letters drawn · previously used letters fade out.</p><form method='post'><button name='action' value='draw'>🎲 Draw a letter</button> <button class='secondary' name='action' value='reset'>New game setup</button></form></section>"
    return page(content + f"<section class='card'><h2>Scoreboard</h2>{rows}</section><section class='card'><h2>Recent turns</h2>{history or '<p class=muted>No turns yet.</p>'}</section>")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        pass  # Player names and answers must not be written to server logs.

    def send_app_headers(self) -> None:
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")

    def do_GET(self) -> None:
        self.send_response(200); self.send_app_headers(); self.end_headers(); self.wfile.write(render())

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        # Protect the local server from cross-site form posts and oversized bodies.
        host = self.headers.get("Host", "")
        if not (host.startswith("127.0.0.1:") or host.startswith("localhost:")) or size > 16384:
            self.send_error(403); return
        fields = parse_qs(self.rfile.read(size).decode("utf-8", "replace"), keep_blank_values=True)
        val = lambda key, default="": fields.get(key, [default])[0]
        action = val("action")
        try:
            if action == "add_player":
                settings = DATA.get("settings") or {"players": [{"name":"Player 1","color":"#f97316"},{"name":"Player 2","color":"#3b82f6"}],"categories":list(DEFAULT_CATEGORIES)}
                settings["players"].append({"name":f"Player {len(settings['players'])+1}","color":"#22c55e"})
                DATA["settings"] = settings
            elif action == "start":
                names, colors = fields.get("player_name", []), fields.get("player_color", [])
                settings = {"players":[{"name":n,"color":colors[i] if i<len(colors) else "#f97316"} for i,n in enumerate(names) if n.strip()],
                    "categories":[c.strip() for c in val("categories", ",".join(DEFAULT_CATEGORIES)).split(",") if c.strip()],
                    "timer_seconds":int(val("timer", "60")), "round_limit":val("round_limit") or None,
                    "exclude_hard_letters":"hard" in fields, "category_mode":"spin" if "spin" in fields else "sequence"}
                DATA["settings"] = settings; DATA["active_game"] = new_game(settings)
            elif action == "draw":
                draw_letter(DATA["active_game"])
            elif action in ("accept", "reject"):
                submit_answer(DATA["active_game"], val("answer"), action == "accept")
            elif action == "refresh" and DATA.get("active_game", {}).get("pending_turn"):
                DATA["active_game"]["pending_turn"]["answer_draft"] = val("answer")
            elif action in ("reset", "new"):
                if DATA.get("active_game"):
                    DATA.setdefault("past_games", []).append(DATA["active_game"])
                DATA["active_game"] = None
        except (ValueError, KeyError, TypeError) as exc:
            self.send_response(400); self.send_app_headers(); self.end_headers(); self.wfile.write(page(f"<section class='card'><h2>Couldn't complete that action</h2><p>{esc(exc)}</p><a href='/'>Return to game</a></section>")); return
        save_data(DATA)
        self.send_response(303); self.send_header("Location", "/"); self.end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"Alphabet Categories is running at http://{HOST}:{PORT} (Ctrl+C to stop)")
    try:
        webbrowser.open(f"http://{HOST}:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
