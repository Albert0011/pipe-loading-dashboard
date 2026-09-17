"""Pure, independently testable pipe loading calculations. Units: mm, m, kg."""
from dataclasses import dataclass, asdict
from math import floor, ceil, pi, sqrt, isfinite
import json
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    length_mm: float = 12032
    width_mm: float = 2352
    height_mm: float = 2395
    door_width_mm: float = 2340
    door_height_mm: float = 2292
    payload_kg: float = 25000
    dunnage_kg: float = 500
    end_clearance_mm: float = 20
    side_clearance_mm: float = 50
    top_clearance_mm: float = 50
    gap_mm: float = 0

def catalogue():
    return json.loads(Path(__file__).with_name('pipe_data.json').read_text(encoding='utf-8'))

def layout(width, height, diameter, gap=0, packing='Best regular pattern'):
    """Compare square and two staggered orientations; not a global circle optimum."""
    if min(width, height) < diameter:
        return {'count': 0, 'rows': 0, 'a': 0, 'b': 0, 'pitch': diameter+gap, 'rotated': False, 'pattern': 'No fit'}
    pitch = diameter + gap
    candidates = []
    modes = ['Square'] if packing == 'Square' else ['Square', 'Staggered']
    for mode in modes:
        for rotated in (False, True):
            w, h = (height, width) if rotated else (width, height)
            rise = pitch if mode == 'Square' else pitch*sqrt(3)/2
            rows = 1 + floor((h-diameter+1e-8)/rise)
            a = 1 + floor((w-diameter+1e-8)/pitch)
            b = a if mode == 'Square' else max(0, 1 + floor((w-diameter-pitch/2+1e-8)/pitch))
            candidates.append(dict(count=ceil(rows/2)*a+floor(rows/2)*b, rows=rows, a=a, b=b, pitch=pitch, rise=rise, rotated=rotated, pattern=mode))
    return max(candidates, key=lambda c:c['count'])

def centers(plan, diameter):
    for row in range(plan['rows']):
        n = plan['a'] if row % 2 == 0 else plan['b']
        offset = plan['pitch']/2 if plan['pattern']=='Staggered' and row % 2 else 0
        for col in range(n):
            x, y = diameter/2+col*plan['pitch']+offset, diameter/2+row*plan['rise']
            yield (y,x) if plan['rotated'] else (x,y)

def calculate(pipe, length_m, density, settings=Settings(), packing='Best regular pattern'):
    s = settings
    values = asdict(s)
    if not all(isfinite(v) and v >= 0 for v in values.values()):
        raise ValueError('Container inputs must be finite and non-negative.')
    if not isfinite(length_m) or not isfinite(density) or length_m <= 0 or density <= 0:
        raise ValueError('Pipe length and density must be positive.')
    if s.dunnage_kg >= s.payload_kg:
        raise ValueError('Dunnage must be less than the payload limit.')
    width=min(s.width_mm,s.door_width_mm)-s.side_clearance_mm
    height=min(s.height_mm,s.door_height_mm)-s.top_clearance_mm
    length=s.length_mm-s.end_clearance_mm
    if min(width,height,length)<=0:
        raise ValueError('Clearances leave no usable container space.')
    od, wall = pipe['od_mm'], pipe['wall_mm']
    if not 0 < 2*wall < od:
        raise ValueError('Pipe wall must leave a positive bore.')
    kg_m = pi*wall*(od-wall)*density/1e6
    kg_piece = kg_m*length_m
    plan=layout(width,height,od,s.gap_mm,packing)
    axial=floor((length+1e-8)/(length_m*1000))
    geometry=plan['count']*axial
    by_weight=floor((s.payload_kg-s.dunnage_kg)/kg_piece)
    pieces=min(geometry,by_weight)
    reason='Pipe length' if axial==0 else ('Cross-section' if plan['count']==0 else ('Geometry' if geometry<by_weight else ('Payload' if by_weight<geometry else 'Both')))
    return dict(pieces=pieces, tonnes=pieces*kg_piece/1000, kg_m=kg_m, kg_piece=kg_piece, geometry=geometry, by_weight=by_weight, limiting=reason, axial=axial, plan=plan, width=width, height=height, length=length, length_margin=length-axial*length_m*1000, payload_utilization=pieces*kg_piece/(s.payload_kg-s.dunnage_kg), settings=values)

def order_cost(result, order, freight):
    containers=ceil(order/result['pieces']) if result['pieces'] else None
    return dict(containers=containers, total_freight=containers*freight if containers is not None else None, freight_per_piece=containers*freight/order if containers is not None and order else None, last_container=(order-(containers-1)*result['pieces']) if containers else 0)
