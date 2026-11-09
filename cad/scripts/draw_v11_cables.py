"""Draw the checked power-cable centerline as an SVG plan view."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
report = json.loads((ROOT/'cad/v11/cable-clearance.json').read_text())


def point(x, y):
    return 340+3*x, 210.5-3.5*y


def rect(x0, y0, x1, y1, **attrs):
    x, y = point(x0, y1)
    extra = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<rect x="{x:g}" y="{y:g}" width="{3*(x1-x0):g}" height="{3.5*(y1-y0):g}" {extra}/>'


path = ' '.join(f'{x:.2f},{y:.2f}' for x, y in
                (point(p[0], p[1]) for p in report['route_centerline_mm']))
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="580" viewBox="0 0 1280 580">
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#202824}}.title{{font-size:27px;font-weight:700}}.label{{font-size:18px}}.note{{font-size:16px;fill:#4a5652}}</style>
<rect width="1280" height="580" fill="#faf9f4"/>
<text x="60" y="45" class="title">Power cable route • v11</text>
<text x="60" y="75" class="note">Plan view from above. Vertical positions are omitted; this is a clearance guide.</text>
{rect(0, 23, 214, 31, fill='#c7beb2')}
<text x="660" y="110" text-anchor="middle" class="note">Wall behind the enclosure</text>
{rect(0, -16.2, 214, 22.4, fill='#e1e5e1', stroke='#59645e', stroke_width=2)}
{rect(2.4, -14.2, 211.6, 20, fill='#faf9f4')}
{rect(-.5, -13.8, 3.2, 20.5, fill='#faf9f4')}
{rect(210.8, -13.8, 214.5, 18, fill='#faf9f4')}
{rect(8, -9.6, 123, 19.4, fill='#e8cb5e', stroke='#a88d34', stroke_width=1.5, rx=14)}
<text x="536" y="187" text-anchor="middle" class="label">INIU battery</text>
<text x="536" y="214" text-anchor="middle" class="note">Ports face left</text>
{rect(146, -2, 202, 15.6, fill='#add2b0', stroke='#497e51', stroke_width=1.5)}
<text x="862" y="192" text-anchor="middle" class="label">Pi 4</text>
{rect(-27.1, -.1, 7.9, 9.9, fill='#465457', rx=3)}
{rect(203.1, 7.4, 238.1, 17.4, fill='#465457', rx=3)}
<polyline points="{path}" fill="none" stroke="#1785b6" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M 252 156 L 281 175" fill="none" stroke="#59645e" stroke-width="1.5"/>
<text x="80" y="149" class="label">USB-A output</text>
<path d="M 1084 128 L 1037 151" fill="none" stroke="#59645e" stroke-width="1.5"/>
<text x="1050" y="116" class="label">Pi USB-C power</text>
<text x="140" y="385" class="label">20 mm bend radius</text>
<text x="970" y="385" class="label">23.75 mm radius</text>
<text x="640" y="309" text-anchor="middle" class="note">Front / room side</text>
<text x="640" y="373" text-anchor="middle" class="label">External flexible power lead</text>
<line x1="60" y1="420" x2="1220" y2="420" stroke="#d1d5ce"/>
<text x="60" y="454" class="label">Battery charging stays accessible through the left opening.</text>
<text x="60" y="482" class="note">35 × 16 × 10 mm plug envelopes; approximately {report['power_route_including_housings_mm']:.0f} mm route including housings.</text>
<text x="60" y="510" class="note">Use a 0.5 m lead if it fits without tension; use a longer standard lead and retain the excess if needed.</text>
<text x="60" y="538" class="note">Port centers and housings are assumptions. Check the actual plugs, ribbon and cable bends on the bench.</text>
</svg>'''
target = ROOT/'docs/hardware/v11/cable-route.svg'
target.write_text(svg+'\n')
print(target)
