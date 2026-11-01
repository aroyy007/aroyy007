#!/usr/bin/env python3
"""Draw Arijit's Signal Harbor from an official Git Koi snapshot and public repos."""

import argparse
from datetime import date, datetime, timedelta
from html import escape
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
LOGIN = 'aroyy007'
FEATURED = [
    ('ML_Study_Buddy', 'ML STUDY', 'BUDDY', 'ai'),
    ('AcademiaConnect', 'ACADEMIA', 'CONNECT', 'campus'),
    ('Air_Quality_Monitoring_System', 'AIR QUALITY', 'MONITOR', 'sensor'),
    ('FedAdapt-EF-Adaptive-Compression-with-Error-Feedback-for-Efficient-DR-Federated-Learning', 'FEDADAPT', 'RESEARCH', 'ai'),
    ('AcademiaConnectApp', 'CAMPUS', 'MOBILE', 'campus'),
    ('FloodGuard_Aid_Network', 'FLOODGUARD', 'AID', 'sensor'),
    ('Ar_Portfolio', 'PORTFOLIO', 'WEB', 'web'),
    ('Problem_Solving_Archive', 'ALGORITHM', 'ARCHIVE', 'web'),
]
PHASES = ('dawn', 'day', 'dusk', 'night')


def build_model(snapshot, repositories):
    if snapshot.get('account_id') != 120275227:
        raise ValueError('Expected the public snapshot for aroyy007.')
    history = snapshot['contribution_history']
    observed = date.fromisoformat(history['observed_on'])
    days = {}
    for day in history['days']:
        stamp = date.fromisoformat(day['date'])
        count = day['contribution_count']
        if type(count) is not int or count < 0 or stamp > observed:
            raise ValueError('Invalid daily contribution observation.')
        if stamp in days and days[stamp] != count:
            raise ValueError('Conflicting daily contribution observations.')
        days[stamp] = count
    if days:
        if max(days) != observed or len(days) != (observed - min(days)).days + 1:
            raise ValueError('Contribution history has a gap.')
    public = {repo['name']: repo for repo in repositories
              if repo.get('private') is False and repo.get('fork') is False}
    buildings = []
    for name, label, label2, kind in FEATURED:
        if name in public:
            repo = public[name]
            size = repo.get('size', 0)
            if type(size) is not int or size < 0:
                raise ValueError('Invalid repository size.')
            buildings.append({'name': name, 'label': label, 'label2': label2,
                              'kind': kind, 'size': size,
                              'language': str(repo.get('language') or 'Not specified')})
    recent = [count for stamp, count in days.items()
              if stamp >= observed - timedelta(days=29)]
    return {
        'login': LOGIN,
        'observed_on': observed.isoformat(),
        'total': sum(days.values()),
        'recent': sum(recent),
        'active_days': sum(count > 0 for count in recent),
        'public_repos': len(public),
        'buildings': buildings,
        'days': {stamp.isoformat(): count for stamp, count in sorted(days.items())},
    }


def render(model, phase, theme):
    dark = theme == 'dark'
    bg, text, muted, outline, water, wall = (
        ('#111718', '#f7f5ed', '#a6b6b3', '#435553', '#14282d', '#223336') if dark else
        ('#fffdf5', '#161d20', '#52615d', '#8eaaa1', '#d9ece7', '#e5e9db'))
    skies = {'dawn': ('#283438', '#f5c590'), 'day': ('#203b40', '#f1fb55'),
             'dusk': ('#3e323a', '#efb079'), 'night': ('#111e29', '#d3e1d4')}
    light_skies = {'dawn': '#f5e8d4', 'day': '#e8f1df', 'dusk': '#efdfd8', 'night': '#e0e5e9'}
    sky, sun = skies[phase]
    if not dark:
        sky = light_skies[phase]
    yellow = '#f1fb55'
    accent_ink = '#17201b'
    observed = date.fromisoformat(model['observed_on'])
    desc = (f"Signal Harbor, an original Chattogram-inspired project city for {LOGIN}. "
            f"{model['total']} contributions through {observed.isoformat()}, "
            f"{model['public_repos']} public non-fork repositories, "
            f"{model['recent']} contributions in the last 30 complete days. "
            'Building height follows repository size; the waterfront is a contribution calendar.')
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560" role="img" aria-labelledby="title desc">',
           '<title id="title">Signal Harbor · Arijit Roy</title>',
           f'<desc id="desc">{escape(desc)}</desc>',
           '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}'
           '@media(prefers-reduced-motion:reduce){.moving{display:none}}</style>',
           f'<rect x="1" y="1" width="1198" height="558" fill="{bg}" stroke="{outline}" stroke-width="2"/>',
           f'<text x="36" y="43" fill="{text}" font-size="27" font-weight="800" letter-spacing="2">SIGNAL HARBOR</text>',
           f'<text x="36" y="70" fill="{muted}" font-size="13">CHATTOGRAM / A CITY OF PROJECTS, MODELS &amp; SIGNALS</text>',
           f'<rect x="951" y="25" width="211" height="31" fill="{yellow}"/>',
           f'<text x="1056" y="46" fill="{accent_ink}" font-size="12" font-weight="700" text-anchor="middle">{phase.upper()} / UTC+06</text>',
           f'<rect x="22" y="91" width="1156" height="310" fill="{sky}"/>']
    # Hills and port cranes reference Chattogram without copying a specific skyline.
    hills = '#314943' if dark else '#becfbc'
    out += [f'<path d="M22 264L97 230L161 247L238 203L330 252L412 218L492 258L580 210L666 249L741 215L829 252L914 219L1008 251L1101 210L1178 242V401H22Z" fill="{hills}"/>',
            f'<circle cx="1056" cy="151" r="26" fill="{sun}"/>']
    if phase == 'night':
        out.append(f'<circle cx="1067" cy="141" r="24" fill="{sky}"/>')
        for x, y in ((95, 125), (314, 151), (517, 114), (702, 143), (887, 120), (1141, 185)):
            out.append(f'<rect x="{x}" y="{y}" width="3" height="3" fill="{sun}"/>')
    crane = '#61736a' if dark else '#92aa95'
    for x, height in ((132, 126), (1002, 149)):
        out.append(f'<path d="M{x} 338V{338-height}h93M{x} {338-height}l-34 39h126M{x+55} {338-height}v62" fill="none" stroke="{crane}" stroke-width="4"/>')
    for index, repo in enumerate(model['buildings']):
        x = 48 + index * 143
        h = 62 + min(102, round(math.log2(repo['size'] + 1) * 6))
        y = 343 - h
        title = escape(f"{repo['name']} · {repo['language']} · {repo['size']:,} KB repository size")
        out += [f'<g><title>{title}</title>',
                f'<rect x="{x+7}" y="{y+8}" width="106" height="{h}" fill="{accent_ink}" opacity="0.3"/>',
                f'<rect x="{x}" y="{y}" width="106" height="{h}" fill="{wall}" stroke="{text}" stroke-width="1.5"/>',
                f'<rect x="{x}" y="{y}" width="106" height="19" fill="{yellow}"/>',
                f'<text x="{x+53}" y="{y+13}" fill="{accent_ink}" font-size="9" font-weight="700" text-anchor="middle">{escape(repo["kind"].upper())} / {index+1:02}</text>']
        for row in range(max(1, (h-40)//22)):
            for col in range(4):
                lit = ((index + row + col) % 3 != 0)
                fill = (yellow if dark else '#7d8b33') if lit else outline
                out.append(f'<rect x="{x+14+col*21}" y="{y+31+row*22}" width="10" height="10" fill="{fill}" opacity="0.8"/>')
        if repo['kind'] == 'sensor':
            out += [f'<path d="M{x+53} {y}v-27m-10 10q10-12 20 0m-16 5q6-8 12 0" fill="none" stroke="{text}" stroke-width="2"/>',
                    f'<circle cx="{x+53}" cy="{y-28}" r="3" fill="{yellow}"/>']
        elif repo['kind'] == 'ai':
            out.append(f'<path d="M{x+16} {y}v-15h73V{y}" fill="none" stroke="{text}" stroke-width="2"/>')
        elif repo['kind'] == 'campus':
            out.append(f'<path d="M{x-5} {y}l58-23 58 23" fill="none" stroke="{text}" stroke-width="3"/>')
        out += [f'<text x="{x+53}" y="367" fill="{text}" font-size="11" font-weight="700" text-anchor="middle">{repo["label"]}</text>',
                f'<text x="{x+53}" y="383" fill="{muted}" font-size="10" text-anchor="middle">{repo["label2"]}</text></g>']
    out += [f'<path d="M22 399H1178" stroke="{outline}" stroke-width="3"/>',
            f'<rect x="22" y="411" width="1156" height="127" fill="{water}"/>',
            f'<text x="38" y="449" fill="{text}" font-size="27" font-weight="800">{model["total"]:,}</text>',
            f'<text x="38" y="470" fill="{muted}" font-size="11">LIFETIME CONTRIBUTIONS</text>',
            f'<text x="38" y="496" fill="{text}" font-size="12">{model["public_repos"]} PUBLIC NON-FORK REPOS</text>',
            f'<text x="38" y="517" fill="{muted}" font-size="11">{model["recent"]} CONTRIBUTIONS / LAST 30D</text>',
            f'<text x="288" y="435" fill="{muted}" font-size="11">WATERFRONT LIGHTS / LAST YEAR / ONE LIGHT PER DAY</text>']
    start = observed - timedelta(days=364)
    start -= timedelta(days=(start.weekday()+1) % 7)
    colors = ('#263b3e', '#5e7136', '#8ea548', '#c4d653', yellow) if dark else ('#c4d7d0', '#aeba77', '#8a9e44', '#667e28', '#405514')
    for offset in range((observed-start).days+1):
        stamp = start + timedelta(days=offset)
        count = model['days'].get(stamp.isoformat())
        level = 0 if not count else min(4, 1 + (count >= 3) + (count >= 6) + (count >= 10))
        x, y = 288 + (offset//7)*16, 449 + (offset%7)*10
        if count is not None:
            out.append(f'<rect x="{x}" y="{y}" width="11" height="7" fill="{colors[level]}"><title>{stamp}: {count} contributions</title></rect>')
    out += [f'<path d="M22 407H1178" stroke="{yellow}" stroke-width="2" stroke-dasharray="4 16"/>',
            f'<rect class="moving" y="403" width="11" height="5" fill="{yellow}"><animate attributeName="x" values="22;1160;22" dur="38s" repeatCount="indefinite"/></rect>',
            f'<text x="38" y="552" fill="{muted}" font-size="10">PUBLIC GITHUB DATA THROUGH {observed.isoformat()} / BUILDING HEIGHT = REPOSITORY SIZE</text>',
            '</svg>']
    return '\n'.join(out)


def render_activity(model, theme):
    dark = theme == 'dark'
    bg, text, muted, grid, line = (
        ('#111718', '#f7f5ed', '#a6b6b3', '#30413f', '#f1fb55') if dark else
        ('#fffdf5', '#17201b', '#52615d', '#dce4d8', '#68791d'))
    observed = date.fromisoformat(model['observed_on'])
    days = [observed - timedelta(days=30-index) for index in range(31)]
    values = [model['days'].get(stamp.isoformat()) for stamp in days]
    known = [value for value in values if value is not None]
    ceiling = max(4, math.ceil(max(known, default=0) / 4) * 4)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="title desc">',
           '<title id="title">Arijit’s GitHub activity · last 31 days</title>',
           f'<desc id="desc">{sum(known)} contributions across {len(known)} observed days in the 31-day window ending {observed}.</desc>',
           '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
           f'<rect width="1200" height="300" fill="{bg}"/>',
           f'<text x="35" y="32" fill="{text}" font-size="19" font-weight="700">GITHUB ACTIVITY / LAST 31 DAYS</text>',
           f'<text x="1160" y="32" fill="{muted}" font-size="12" text-anchor="end">{sum(known)} CONTRIBUTIONS</text>']
    for tick in range(5):
        value = ceiling * tick // 4
        y = 230 - tick * 42
        out += [f'<path d="M65 {y}H1160" stroke="{grid}" stroke-width="1"/>',
                f'<text x="49" y="{y+4}" fill="{muted}" font-size="11" text-anchor="end">{value}</text>']
    segments = []
    segment = []
    for index, (stamp, value) in enumerate(zip(days, values)):
        x = 65 + index * 1095 / 30
        if value is None:
            if segment:
                segments.append(segment)
                segment = []
        else:
            y = 230 - value / ceiling * 168
            segment.append((x, y, stamp, value))
        if index % 5 == 0:
            out.append(f'<text x="{x:.1f}" y="252" fill="{muted}" font-size="11" text-anchor="middle">{stamp.strftime("%d %b")}</text>')
    if segment:
        segments.append(segment)
    for segment in segments:
        points = ' '.join(f'{x:.1f},{y:.1f}' for x, y, _, _ in segment)
        out += [f'<polygon points="{segment[0][0]:.1f},230 {points} {segment[-1][0]:.1f},230" fill="{line}" opacity="0.12"/>',
                f'<polyline points="{points}" fill="none" stroke="{line}" stroke-width="2.5"/>']
        for x, y, stamp, value in segment:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{line}" data-date="{stamp}" data-count="{value}"><title>{stamp}: {value} contributions</title></circle>')
    out += [f'<text x="35" y="284" fill="{muted}" font-size="10">PUBLIC GITHUB DATA / THROUGH {observed} / UPDATED WITH SIGNAL HARBOR</text>', '</svg>']
    return '\n'.join(out)


def fetch_repositories():
    repositories = []
    page = 1
    headers = {'User-Agent': 'aroyy007-signal-harbor', 'Accept': 'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    while True:
        url = f'https://api.github.com/users/{LOGIN}/repos?per_page=100&type=owner&page={page}'
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError('Expected a public repository list from GitHub.')
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--repositories', type=Path, help='Use a saved public REST repository response, for offline rendering.')
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    repos = json.loads(args.repositories.read_text()) if args.repositories else fetch_repositories()
    model = build_model(snapshot, repos)
    hour = datetime.now(ZoneInfo('Asia/Dhaka')).hour
    current = 'dawn' if 5 <= hour < 8 else 'day' if 8 <= hour < 17 else 'dusk' if 17 <= hour < 19 else 'night'
    outputs = {}
    for theme in ('light', 'dark'):
        outputs[ROOT / 'assets' / f'activity-{theme}.svg'] = render_activity(model, theme)
    for phase in PHASES:
        for theme in ('light', 'dark'):
            svg = render(model, phase, theme)
            outputs[ROOT / 'assets' / 'harbor' / f'{phase}-{theme}.svg'] = svg
            if phase == current:
                outputs[ROOT / 'assets' / 'harbor' / f'current-{theme}.svg'] = svg
        outputs[ROOT / 'views' / f'{phase}.md'] = f'''# Signal Harbor · {phase.title()}

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/harbor/{phase}-dark.svg">
  <img src="../assets/harbor/{phase}-light.svg" width="100%" alt="Arijit's Chattogram-inspired project city at {phase}">
</picture>

[Dawn](dawn.md) · [Day](day.md) · [Dusk](dusk.md) · [Night](night.md) · [Back to my profile](../README.md#signal-harbor)

{model['total']:,} lifetime contributions · {model['public_repos']} public non-fork repositories · {model['recent']} contributions in the last 30 complete days.

The buildings represent my featured repositories. Their heights follow repository size in KB. The waterfront lights show daily contributions, through {model['observed_on']}.

Original artwork and generator for [Arijit Roy](https://github.com/{LOGIN}), inspired by [Vineet's Commit City](https://github.com/vineetjk/vineetjk).
'''
    outputs[ROOT / 'data' / 'harbor.json'] = json.dumps(model, indent=2) + '\n'
    # Finish collection and rendering before replacing the last successful assets.
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(content)
        temporary.replace(path)
    print(f"Signal Harbor: {model['total']:,} lifetime contributions, {model['public_repos']} public non-fork repositories; {current} in Asia/Dhaka.")


if __name__ == '__main__':
    main()
