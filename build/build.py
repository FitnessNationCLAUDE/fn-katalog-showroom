#!/usr/bin/env python3
"""fitness nation | Katalog-Showroom — alternative Katalog-Ansicht.
Konzept: fester nummerierter Produkt-Index links (mit Preisen, filterbar
Software/Hardware), rechts volle Produkt-Spreads mit Bildbühne + Spec-Grid
(Datenblatt-Ästhetik). Gleiche Inhalts-JSONs + Brain-Preise wie der Hauptkatalog.

  python3 build/build.py          → site/de, site/en, site/de/smart, site/en/smart
"""
import json, html, os, time
try:
    from PIL import Image as _PIL
except Exception:
    _PIL = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = "/home/claude/Claude/_WISSENSDATENBANK"
DOMAIN = "https://fn-katalog-showroom.vercel.app"
BUILD_V = str(int(time.time()))

def esc(t): return html.escape(str(t), quote=True)

def nl(t): return esc(t)

_dims = {}
def dims(rel):
    if not rel or _PIL is None: return ""
    if rel in _dims: return _dims[rel]
    try:
        w, h = _PIL.open(os.path.join(ROOT, "site", rel.lstrip("/"))).size
        r = f' width="{w}" height="{h}"'
    except Exception:
        r = ""
    _dims[rel] = r
    return r

# ---------------------------------------------------------------- Preise (Brain)
def _load_pricing():
    pmap = json.load(open(f"{ROOT}/content/PRICING_MAP.json"))
    hw = {p.get("article_number"): p for p in json.load(open(f"{KB}/FN_HARDWARE_MASTERDATA.json"))["products"] if p.get("article_number")}
    md = json.load(open(f"{KB}/FN_MASTERDATA.json"))
    sw = {a["item_number"]: a for a in md["articles"]}
    return pmap, hw, sw, md.get("music_licenses", [])
PRICING = _load_pricing()

def _eur(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def price_rows(cat_name, sid, lang):
    """[(name, artnr, preis_html)] aus dem Brain."""
    pmap, hw, sw, music = PRICING
    t_mon = "/ Monat" if lang == "de" else "/ month"
    rows, notes = [], []
    for ref in pmap.get(cat_name, {}).get(sid) or []:
        if ref == "music":
            for m in music:
                rows.append(("fitness nation | Music — " + m["position"], "FN-SP-5100", f'{esc(m["net_price_de"])} <small>{t_mon}</small>'))
            continue
        kind, num = ref.split(":", 1)
        if kind == "sw":
            a = sw.get(num)
            if not a: continue
            price = a["net_price_de"]
            if "brutto" in price:
                p0 = price.split(" brutto")[0].strip()
                extra = "brutto / aktiver Nutzer" if lang == "de" else "gross / active user"
                rows.append((a["name"], num, f'{esc(p0)} <small>{extra}</small>'))
            else:
                unit = t_mon if a.get("billing_cycle") == "monatlich" else esc(a.get("billing_cycle", ""))
                rows.append((a["name"], num, f'{esc(price)} <small>{unit}</small>'))
        else:
            pr = hw.get(num)
            if not pr: continue
            amt = ((pr.get("pricing") or {}).get("rrp_eu_net") or {}).get("amount")
            if amt is not None and (pr.get("pricing") or {}).get("included_with"):   # K-0032: z. B. Bezahlterminal, bei Smart Vending inklusive
                rows.append((pr["display_name"], num, ("inklusive <small>bei Smart Vending · Wert %s UVP</small>" if lang == "de" else "included <small>with Smart Vending · value %s RRP</small>") % _eur(amt)))
                continue
            if amt is None:
                rows.append((pr["display_name"], num, "auf Anfrage" if lang == "de" else "on request"))
            else:
                rows.append((pr["display_name"], num, f'{_eur(amt)} <small>UVP</small>' if lang == "de" else f'{_eur(amt)} <small>RRP</small>'))
            sb = (pr.get("pricing") or {}).get("subscription")   # K-0032 / Owner 14.10.2026 (N47): Subscription, kein Ratenkauf
            if sb:
                _de = lang == "de"
                _m = "Monat" if _de else "month"
                _txt = ("{} auch als Subscription über {} Monate: {} Anzahlung + {} × {} / {}" if _de else
                        "{} also as a {}-month subscription: {} down payment + {} × {} / {}").format(
                    pr.get("short_name") or pr["display_name"], sb["laufzeit_monate"], _eur(sb["anzahlung_eur"]), sb["laufzeit_monate"], _eur(sb["subscription_gebuehr_monat_eur"]), _m)
                for _d in sb.get("dazu_monatlich") or []:
                    _txt += " + {} {} / {}".format(_d["name"], _eur(_d["betrag_eur"]), _m)
                _txt += "."
                if sb.get("dazu_monatlich"):
                    _txt += (" Danach nur {} {} / Monat." if _de else " Afterwards only {} {} / month.").format(sb["dazu_monatlich"][0]["name"], _eur(sb["dazu_monatlich"][0]["betrag_eur"]))
                for _i in sb.get("inklusive") or []:
                    _txt += (" {} inklusive." if _de else " {} included.").format(_i["name"])
                if sb.get("lieferzeit"):
                    _w = sb["lieferzeit"].split()[0]
                    _txt += (" Lieferzeit {} Wochen." if _de else " Delivery time {} weeks.").format(_w)
                notes.append(_txt)
            sk = (pr.get("pricing") or {}).get("subscription_kauf")
            if sk and sid == "bodycheck":
                notes.append(("Auch als Subscription-Kauf: {} Anzahlung + {} × {} / Monat."
                              if lang == "de" else
                              "Also available as subscription purchase: {} down payment + {} × {} / month.")
                             .format(_eur(sk["anzahlung_eur"]), sk["anzahl_raten"], _eur(sk["monatliche_rate_eur"])))
    return rows, notes

def price_chip(cat_name, sid, lang):
    rows, _ = price_rows(cat_name, sid, lang)
    if not rows: return None
    import re
    first = rows[0][2]
    return re.sub(r"<small>", " <small>", first, count=1)

# ---------------------------------------------------------------- Produkt-Metadaten
MEDIA = {
    "gesamt": {
        "membership": ("screen", "app_profile.webp"), "manager": ("chat", None),
        "dashboard": ("screen", "app_score.webp"), "app": ("screen", "app_home.webp"),
        "coach": ("screen", "app_coach.webp"), "trainer": ("screen", "app_health.webp"),
        "bodycheck": ("cutout", "bodycheck_1200.png"), "terminal": ("cutout", "kiosk.webp"),
        "vending-nutrition": ("cutout", "vending.webp"), "tv": ("cutout", "screens.webp"),
        "locks-gates-access": ("cutout", "gates.webp"),
    },
    "smart": {
        "coach": ("screen", "app_coach.webp"), "nutrition-ai": ("screen", "app_nutrition.webp"),
        "training-ai": ("screen", "app_chat.webp"), "bodycheck": ("cutout", "bodycheck_1200.png"),
        "trainer": ("screen", "app_health.webp"), "kiosk": ("cutout", "kiosk.webp"),
        "screens": ("cutout", "screens.webp"), "vending": ("cutout", "vending.webp"),
        "locks": ("cutout", "locks.webp"), "gates-access": ("cutout", "gates.webp"),
    },
}
EXTRA = {"gesamt": {"tv": "tvstick.webp", "vending-nutrition": "nutritionbox.webp"},
         "smart": {"vending": "nutritionbox.webp"}}
HARDWARE = {"gesamt": {"bodycheck", "terminal", "vending-nutrition", "tv", "locks-gates-access"},
            "smart": {"bodycheck", "kiosk", "screens", "vending", "locks", "gates-access"}}

def prodname(k):
    if "|" in (k or ""):
        a, b = k.split("|", 1)
        return f'<span translate="no">{esc(a.strip())} <span class="pipe">|</span> <b>{esc(b.strip())}</b></span>'
    return esc(k or "")

def shortname(k):
    return k.split("|")[-1].strip() if "|" in (k or "") else (k or "")

def first_sentence(s):
    body = s.get("body") or []
    src = s.get("sub") or (body[0] if body else "")
    t = str(src).split(". ")[0].strip()
    return (t + ".") if t and not t.endswith(".") else t

# ---------------------------------------------------------------- Spread-Bausteine
def media_stage(cat_name, s, lang):
    sid = s["id"]
    mode, img = MEDIA.get(cat_name, {}).get(sid, (None, None))
    name = s.get("kicker") or sid
    if mode == "chat":
        rows = ""
        meta = ""
        for b in s.get("blocks") or []:
            if b.get("kind") == "chat":
                for m in b.get("items", []):
                    rows += f'<div class="msg {m.get("from","in")}"><p>{esc(m["text"])}</p></div>'
                if b.get("meta"):
                    meta = f'<div class="chatmeta"><i></i>{esc(b["meta"])}</div>'
        if rows:
            return f'<div class="stage ink chatstage"><div class="chatpanel">{meta}{rows}</div></div>'
        mode, img = ("screen", "app_chat.webp")
    if mode == "screen" and img:
        src = f"/assets/img/{img}"
        return (f'<div class="stage ink"><div class="phone"><div class="scr">'
                f'<img src="{src}" alt="{esc(name)}"{dims(src)} loading="lazy"></div></div></div>')
    if mode == "cutout" and img:
        src = f"/assets/img/{img}"
        ex = EXTRA.get(cat_name, {}).get(sid)
        ex_html = f'<img class="dev2" src="/assets/img/{ex}" alt=""{dims("/assets/img/"+ex)} loading="lazy">' if ex else ""
        return (f'<div class="stage mint"><img class="dev" src="{src}" alt="{esc(name)}"{dims(src)} loading="lazy">{ex_html}</div>')
    word = shortname(name)
    return (f'<div class="stage ink tile"><span class="tpipe" aria-hidden="true">|</span>'
            f'<span class="tword">{esc(word)}</span></div>')

def spec_grid(cat_name, s, lang):
    """Datenblatt-Raster: Kategorie/Abrechnung + Preiszeilen aus dem Brain."""
    sid = s["id"]
    L = {"de": {"cat": "Kategorie", "sw": "Software", "hw": "Hardware", "item": "Artikel",
                "art": "Art.-Nr.", "price": "Preis (netto)", "note": "Alle Preise zzgl. MwSt.; Hardware zzgl. Lieferung.",
                "onreq": "Preis auf Anfrage — im Plattform-Gespräch."},
         "en": {"cat": "Category", "sw": "Software", "hw": "Hardware", "item": "Item",
                "art": "Item no.", "price": "Price (net)", "note": "All prices plus VAT; hardware plus delivery.",
                "onreq": "Price on request — as part of the platform conversation."}}[lang]
    is_hw = sid in HARDWARE.get(cat_name, set())
    rows, notes = price_rows(cat_name, sid, lang)
    cells = f'<div class="cell"><span>{L["cat"]}</span><b>{L["hw"] if is_hw else L["sw"]}</b></div>'
    if rows:
        _inc = [r for r in rows if r[2].startswith(("inklusive", "included"))]   # K-0032: inklusive-Zeilen zählen nicht zur 6er-Grenze
        for n, a, p in [r for r in rows if r not in _inc][:6] + _inc:
            cells += (f'<div class="cell wide"><span translate="no">{esc(n)}</span>'
                      f'<b class="pr">{p}</b><i class="art">{esc(a)}</i></div>')
        note = "".join(f'<p class="note">{esc(n)}</p>' for n in notes) + f'<p class="note">{L["note"]}</p>'
    else:
        cells += f'<div class="cell wide"><span>{L["price"]}</span><b>{L["onreq"]}</b></div>'
        note = ""
    return f'<div class="specs"><div class="specgrid">{cells}</div>{note}</div>'

def feat_block(s, lang):
    items, title = [], None
    ai_items, ai_title = [], None
    for b in s.get("blocks") or []:
        if b.get("kind") == "list" and not items:
            items = b.get("items", []); title = b.get("title")
        if b.get("kind") == "ai_badge":
            ai_items = b.get("items", []); ai_title = b.get("title")
    out = ""
    if items:
        lab = title or ("Funktionen" if lang == "de" else "Features")
        vis = items[:8]; hid = items[8:]
        f_vis = "".join(f"<span>{esc(i)}</span>" for i in vis)
        if hid:
            f_hid = "".join(f"<span>{esc(i)}</span>" for i in hid)
            more = ("Alle %d anzeigen" % len(items)) if lang == "de" else ("Show all %d" % len(items))
            less = "Weniger anzeigen" if lang == "de" else "Show less"
            out += (f'<div class="feats"><h4>{esc(lab)}</h4><div class="flist">{f_vis}'
                    f'<span class="fhid">{f_hid}</span></div>'
                    f'<button type="button" class="fmore" data-more="{esc(more)}" data-less="{esc(less)}">{esc(more)}</button></div>')
        else:
            out += f'<div class="feats"><h4>{esc(lab)}</h4><div class="flist">{f_vis}</div></div>'
    if ai_items:
        lab = ai_title or "AI-powered"
        f_ai = "".join(f"<span>{esc(i)}</span>" for i in ai_items[:6])
        out += f'<div class="feats ai"><h4>{esc(lab)}</h4><div class="flist">{f_ai}</div></div>'
    return out

def product_spread(cat_name, s, lang, num, total):
    sid = s["id"]
    name = s.get("kicker") or sid
    catg = ("hw" if sid in HARDWARE.get(cat_name, set()) else "sw")
    tagtxt = {"de": {"sw": "Software", "hw": "Hardware"}, "en": {"sw": "Software", "hw": "Hardware"}}[lang][catg]
    body = "".join(f"<p>{esc(p)}</p>" for p in (s.get("body") or [])[:3])
    stmt = f'<p class="statement">{nl(s["statement"])}</p>' if s.get("statement") else ""
    chip = price_chip(cat_name, sid, lang)
    chip_html = f'<span class="chip">{chip}</span>' if chip else ""
    lead = s.get("sub")
    lead_html = f'<p class="plead">{esc(lead)}</p>' if lead else ""
    return f'''<section class="spread product" id="{sid}" data-cat="{catg}">
<header class="phead">
  <span class="num" aria-hidden="true">{num:02d}</span>
  <div class="pname"><span class="tag">{esc(tagtxt)}</span><h2 translate="no">{prodname(name)}</h2></div>
  <span class="count" aria-hidden="true">{num:02d} / {total:02d}</span>
</header>
<div class="pbody">
  {media_stage(cat_name, s, lang)}
  <div class="pinfo">
    {lead_html}
    <div class="pcopy">{body}</div>
    {stmt}
    {chip_html}
    {feat_block(s, lang)}
    {spec_grid(cat_name, s, lang)}
  </div>
</div>
</section>'''

def intro_spread(cat, lang, prods):
    meta = cat["meta"]
    vision = next((s for s in cat["sections"] if s.get("type") == "vision"), None)
    cover = next((s for s in cat["sections"] if s.get("type") == "cover"), None)
    title = (cover or {}).get("headline", meta.get("brand", "fitness nation"))
    sub = (cover or {}).get("sub", "")
    v_head = (vision or {}).get("headline", "")
    v_stmt = (vision or {}).get("statement", "")
    chap_count = sum(1 for s in cat["sections"] if s.get("type") == "chapter")
    t = {"de": ("Produktkatalog", "Produkte", "Kapitel", "Sprachen", "Plattform"),
         "en": ("Product catalog", "Products", "Chapters", "Languages", "Platform")}[lang]
    stats = f'<div class="st"><span>{t[1]}</span><b>{len(prods)}</b></div>'
    if chap_count:
        stats += f'<div class="st"><span>{t[2]}</span><b>{chap_count}</b></div>'
    stats += f'<div class="st"><span>{t[3]}</span><b>DE · EN</b></div><div class="st"><span>{t[4]}</span><b>1</b></div>'
    return f'''<section class="spread intro" id="intro">
<p class="eyebrow"><span translate="no">{prodname(meta.get("brand","fitness nation"))}</span> — {esc(t[0])}</p>
<h1 class="cover-title">{nl(title)}</h1>
<p class="cover-sub">{esc(sub)}</p>
<div class="introgrid">
  <div><h3 class="vhead">{nl(v_head)}</h3></div>
  <div><p class="vstmt">{nl(v_stmt)}</p><div class="stats">{stats}</div></div>
</div>
<p class="scrollhint" aria-hidden="true">↓</p>
</section>'''

def ai_spread(cat, lang):
    ai = next((s for s in cat["sections"] if s.get("type") == "ai"), None)
    if not ai:
        return ""
    body = "".join(f"<p>{esc(p)}</p>" for p in (ai.get("body") or [])[:2])
    stmt = f'<p class="statement">{nl(ai["statement"])}</p>' if ai.get("statement") else ""
    cells = ""
    for b in ai.get("blocks") or []:
        if b.get("kind") == "groups":
            for g in b.get("groups", []):
                its = "".join(f"<span>{esc(i)}</span>" for i in g.get("items", [])[:4])
                cells += f'<div class="cell wide"><span>{esc(g["name"])}</span><div class="flist mini">{its}</div></div>'
    grid = f'<div class="specs"><div class="specgrid ai">{cells}</div></div>' if cells else ""
    lab = {"de": "Die KI-Ebene", "en": "The AI layer"}[lang]
    return f'''<section class="spread aispread" id="ai">
<header class="phead"><span class="num" aria-hidden="true">AI</span>
<div class="pname"><span class="tag">{esc(lab)}</span><h2>{nl(ai.get("headline",""))}</h2></div></header>
<div class="pbody"><div class="pinfo solo">{body}{stmt}{grid}</div></div>
</section>'''

def contact_spread(cat, lang):
    meta = cat["meta"]
    closing = next((s for s in cat["sections"] if s.get("type") == "closing"), None) or {}
    c = meta.get("contact", {})
    cta = closing.get("cta") or {}
    goals = ""
    for b in closing.get("blocks") or []:
        if b.get("kind") == "list":
            goals = "".join(f'<p class="goal">{esc(i)}</p>' for i in b.get("items", []))
    t = {"de": ("Kontakt", "Alle Preise zzgl. MwSt.; Hardware zzgl. Lieferung."),
         "en": ("Contact", "All prices plus VAT; hardware plus delivery.")}[lang]
    lines = "<br>".join(esc(x) for x in (c.get("company"), c.get("street"), c.get("city"), c.get("hotline"), c.get("email")) if x)
    return f'''<section class="spread contact" id="kontakt">
<h2 class="cover-title small">{nl(closing.get("headline",""))}</h2>
<div class="introgrid">
  <div>{goals}</div>
  <div><h4 class="cl">{esc(cta.get("headline",""))}</h4><p class="ctxt">{esc(cta.get("text",""))}</p>
  <h4 class="cl">{t[0]}</h4><p class="ctxt">{lines}</p></div>
</div>
<p class="legal">{t[1]}</p>
<div class="foot-word" translate="no">fitness nation<span class="pipe">|</span></div>
</section>'''

# ---------------------------------------------------------------- Index (linke Leiste)
def index_rail(cat, lang, prods, cat_name):
    t = {"de": ("Index", "Alle", "Software", "Hardware", "Einführung", "KI-Ebene", "Kontakt"),
         "en": ("Index", "All", "Software", "Hardware", "Introduction", "AI layer", "Contact")}[lang]
    chips = (f'<div class="filters" role="group" aria-label="Filter">'
             f'<button class="fbtn on" data-f="all">{t[1]}</button>'
             f'<button class="fbtn" data-f="sw">{t[2]}</button>'
             f'<button class="fbtn" data-f="hw">{t[3]}</button></div>')
    rows = f'<a class="irow meta" href="#intro"><span class="iname">{t[4]}</span></a>'
    chap_for = {}
    cur = None
    for s in cat["sections"]:
        if s.get("type") == "chapter":
            cur = s.get("chapter")
        if s.get("type") == "product":
            chap_for[s["id"]] = cur
    last_ch = None
    for i, s in enumerate(prods, 1):
        ch = chap_for.get(s["id"])
        if ch and ch != last_ch:
            rows += f'<div class="igroup">{esc(ch)}</div>'
            last_ch = ch
        catg = "hw" if s["id"] in HARDWARE.get(cat_name, set()) else "sw"
        chip = price_chip(cat_name, s["id"], lang) or ""
        rows += (f'<a class="irow" href="#{s["id"]}" data-cat="{catg}">'
                 f'<span class="ino">{i:02d}</span>'
                 f'<span class="iname" translate="no">{esc(shortname(s.get("kicker") or s["id"]))}</span>'
                 f'<span class="iprice">{chip}</span></a>')
    rows += f'<a class="irow meta" href="#ai"><span class="iname">{t[5]}</span></a>'
    rows += f'<a class="irow meta" href="#kontakt"><span class="iname">{t[6]}</span></a>'
    return f'<aside class="rail" aria-label="{t[0]}"><div class="rail-head">{t[0]}</div>{chips}<nav class="ilist">{rows}</nav></aside>'

# ---------------------------------------------------------------- Seite
def page(cat, lang, cat_name, paths):
    meta = cat["meta"]
    prods = [s for s in cat["sections"] if s.get("type") == "product"]
    total = len(prods)
    spreads = [intro_spread(cat, lang, prods)]
    spreads += [product_spread(cat_name, s, lang, i, total) for i, s in enumerate(prods, 1)]
    a = ai_spread(cat, lang)
    if a: spreads.append(a)
    spreads.append(contact_spread(cat, lang))
    ui = {"de": {"present": "Präsentation", "menu": "Index"}, "en": {"present": "Present", "menu": "Index"}}[lang]
    other_lang = "en" if lang == "de" else "de"
    other_cat = "smart" if cat_name == "gesamt" else "gesamt"
    cat_label = {"gesamt": {"de": "smart", "en": "smart"}, "smart": {"de": "Gesamtkatalog", "en": "Full catalog"}}[cat_name][lang]
    title = f'{meta.get("brand","fitness nation")} — Showroom' + ("" if cat_name == "gesamt" else " · smart")
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta.get('subline',''))}">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#f1f2f4">
<link rel="alternate" hreflang="{lang}" href="{DOMAIN}{paths[lang]}">
<link rel="alternate" hreflang="{other_lang}" href="{DOMAIN}{paths[other_lang]}">
<link rel="alternate" hreflang="x-default" href="{DOMAIN}{paths['de']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta.get('subline',''))}">
<meta property="og:locale" content="{'de_DE' if lang=='de' else 'en_US'}">
<link rel="preload" as="font" type="font/woff2" href="/assets/fonts/outfit.woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/showroom.css?v={BUILD_V}">
</head>
<body>
<header class="topbar">
  <button class="menubtn" id="menubtn" aria-expanded="false" aria-controls="railwrap">☰ {ui["menu"]}</button>
  <a class="brand" href="#intro" translate="no">{prodname(meta.get("brand","fitness nation"))}</a>
  <div class="topbar-right">
    <a class="tbtn" href="{paths["othercat"]}" translate="no">{esc(cat_label)}</a>
    <a class="tbtn" href="{paths[other_lang]}">{other_lang.upper()}</a>
    <button class="tbtn solid" id="present">{ui["present"]} ⌁ F</button>
  </div>
</header>
<div class="shell">
<div class="railwrap" id="railwrap">{index_rail(cat, lang, prods, cat_name)}</div>
<main>
{chr(10).join(spreads)}
</main>
</div>
<div class="blackout"></div>
<script src="/assets/js/showroom.js?v={BUILD_V}" defer></script>
</body>
</html>'''

def build():
    for cat_name in ("gesamt", "smart"):
        for lang in ("de", "en"):
            cat = json.load(open(f"{ROOT}/content/{cat_name}/{lang}.json"))
            base = {"de": "/de", "en": "/en"} if cat_name == "gesamt" else {"de": "/de/smart", "en": "/en/smart"}
            paths = dict(base)
            paths["othercat"] = ("/de/smart" if lang == "de" else "/en/smart") if cat_name == "gesamt" else ("/de" if lang == "de" else "/en")
            out = f"{ROOT}/site{base[lang]}/index.html"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w").write(page(cat, lang, cat_name, paths))
            print("→", out)

if __name__ == "__main__":
    build()
