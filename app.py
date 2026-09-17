from dataclasses import asdict
from itertools import islice
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import Settings, catalogue, calculate, centers, order_cost

st.set_page_config(page_title='Pipe loading | 40GP', page_icon='📦', layout='wide')
st.markdown('''<style>
.block-container {padding-top:4rem; max-width:1500px;}
h1 {letter-spacing:-1.4px;} [data-testid="stMetric"] {background:white;border:1px solid #dde5ef;border-radius:12px;padding:18px;}
[data-testid="stMetricValue"] {color:#163e63;font-size:26px;} .eyebrow {color:#167D9A;font-size:12px;font-weight:700;letter-spacing:2px;}
</style>''',unsafe_allow_html=True)
rows=catalogue()
with st.sidebar:
    st.markdown('### Shipment specification')
    material=st.selectbox('Material',['Carbon Steel','Stainless Steel'])
    material_rows=[p for p in rows if p['material']==material]
    sizes=sorted(set(p['nps'] for p in material_rows),key=lambda n:next(p['nps_numeric'] for p in material_rows if p['nps']==n))
    nps=st.selectbox('Nominal pipe size (in)',sizes,index=sizes.index('4'))
    candidates=[p for p in material_rows if p['nps']==nps]
    schedules=sorted(set(p['schedule'] for p in candidates),key=lambda x: (999 if x in ['STD','XS','XXS'] else int(x.rstrip('S')),x))
    default='40' if material=='Carbon Steel' else '40S'
    sch=st.selectbox('Schedule',schedules,index=schedules.index(default) if default in schedules else 0)
    pipe=next(p for p in candidates if p['schedule']==sch)
    length=st.number_input('Pipe length (m)',min_value=0.1,max_value=30.0,value=12.0,step=0.1)
    density=st.number_input('Material density (kg/m³)',min_value=1000.0,max_value=20000.0,value=7850.0 if material=='Carbon Steel' else 8000.0,step=10.0)
    packing=st.selectbox('Packing model',['Best regular pattern','Square'])
    st.caption('Valid schedules update with material and size. Custom lengths are supported.')
    values=asdict(Settings())
    with st.expander('Container and loading assumptions'):
        labels={'length_mm':'Internal length (mm)','width_mm':'Internal width (mm)','height_mm':'Internal height (mm)','door_width_mm':'Door width (mm)','door_height_mm':'Door height (mm)','payload_kg':'Maximum planning payload (kg)','dunnage_kg':'Dunnage / securement (kg)','end_clearance_mm':'Total end clearance (mm)','side_clearance_mm':'Total side clearance (mm)','top_clearance_mm':'Total top clearance (mm)','gap_mm':'Gap between pipe surfaces (mm)'}
        for key,value in values.items():
            values[key]=st.number_input(labels[key],min_value=0.0,value=float(value),step=10.0 if key!='gap_mm' else 1.0)
    st.caption('Default equipment: Hapag-Lloyd 40 ft standard example. Verify the booked unit.')

st.markdown('<div class="eyebrow">COMMERCIAL OPERATIONS · SHIPMENT PLANNING</div>',unsafe_allow_html=True)
st.title('Pipe loading, made visible')
st.caption(f'40GP container / {material} / NPS {nps} / Schedule {sch} / {length:g} m pieces')
try:
    result=calculate(pipe,length,density,Settings(**values),packing)
except ValueError as exc:
    st.error(str(exc)); st.stop()
c1,c2=st.columns(2)
c3,c4=st.columns(2)
c1.metric('Estimated pieces',f"{result['pieces']:,}")
c2.metric('Net pipe weight',f"{result['tonnes']:,.2f} t")
c3.metric('Pipe payload used',f"{result['payload_utilization']:.1%}")
c4.metric('Limiting factor',result['limiting'])
if not result['pieces']:
    st.warning('No pieces fit under these assumptions. Review pipe length, dimensions, payload and clearances.')
elif result['length_margin']<50:
    st.info(f"Only {result['length_margin']:.0f} mm remains beyond the specified end clearance across {result['axial']} axial position(s). Confirm actual cut lengths and loading access.")
tabs=st.tabs(['Loading visuals','Compare scenarios','Order and freight','Pipe catalogue','Method and sources'])

def style(fig,title):
    fig.update_layout(title=title,template='plotly_white',paper_bgcolor='rgba(0,0,0,0)',font=dict(family='Arial',color='#192B43'),margin=dict(l=30,r=20,t=55,b=40))
    return fig

with tabs[0]:
    left,right=st.container(),st.container()
    with left:
        plan=result['plan']; od=pipe['od_mm']; inner=od-2*pipe['wall_mm']
        fig=go.Figure()
        fig.add_shape(type='rect',x0=0,y0=0,x1=result['width'],y1=result['height'],line=dict(color='#263E5C',width=3),fillcolor='#F3F7FC')
        # Capacity diagram intentionally does not claim a final load distribution.
        count=plan['count']; cap=600
        shapes=list(fig.layout.shapes)
        for x,y in islice(centers(plan,od),cap):
            shapes.append(dict(type='circle',x0=x-od/2,y0=y-od/2,x1=x+od/2,y1=y+od/2,line=dict(color='#167D9A',width=1),fillcolor='#64B4C6'))
            if count<=200:
                shapes.append(dict(type='circle',x0=x-inner/2,y0=y-inner/2,x1=x+inner/2,y1=y+inner/2,line=dict(width=0),fillcolor='#F3F7FC'))
        fig.update_layout(shapes=shapes)
        fig.update_xaxes(title='Width (mm)',range=[-30,result['width']+30],showgrid=False,constrain='domain')
        fig.update_yaxes(title='Height (mm)',range=[-30,result['height']+30],scaleanchor='x',scaleratio=1,showgrid=False,constrain='domain')
        fig.update_layout(height=470)
        st.plotly_chart(style(fig,'Cross-section capacity'),width='stretch')
        st.caption(f"{plan['pattern']} pattern · {count:,} possible positions per cross-section · {result['axial']} axial positions. This shows geometric capacity, not the payload-limited loading arrangement.")
        if count>cap: st.caption(f'For performance, only the first {cap} pipe outlines are drawn; calculations use all {count:,} positions.')
    with right:
        fig=go.Figure(go.Bar(x=[result['geometry'],result['by_weight'],result['pieces']],y=['Geometry limit','Payload limit','Estimated load'],orientation='h',marker_color=['#A8C5D9','#6A88A9','#167D9A'],text=[result['geometry'],result['by_weight'],result['pieces']],textposition='auto'))
        fig.update_layout(height=290);fig.update_xaxes(title='Pieces')
        st.plotly_chart(style(fig,'What controls this shipment?'),width='stretch')
        st.progress(min(1.0,result['payload_utilization']),text='Share of payload available to pipes')
        st.write(f"**{result['kg_piece']:,.2f} kg** per piece · **{result['kg_m']:,.2f} kg/m**")
        st.caption(f"Outside diameter {od:g} mm · wall {pipe['wall_mm']:g} mm · density {density:,.0f} kg/m³")
        st.caption('Metric tons exclude dunnage. Pipeline / pressure suitability is outside this model.')
    st.markdown('#### Along the container')
    fig=go.Figure()
    fig.add_shape(type='rect',x0=0,y0=0,x1=result['length'],y1=1,line=dict(color='#263E5C'))
    for i in range(result['axial']):
        fig.add_shape(type='rect',x0=i*length*1000,y0=.15,x1=(i+1)*length*1000,y1=.85,fillcolor='#64B4C6',line=dict(color='white'))
    fig.update_layout(height=160,margin=dict(l=20,r=20,t=10,b=35),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='white');fig.update_xaxes(title='Usable container length (mm)',range=[0,result['length']]);fig.update_yaxes(visible=False,range=[-.1,1.1])
    st.plotly_chart(fig,width='stretch')

with tabs[1]:
    st.subheader('Compare before quoting')
    st.caption('Saved scenarios last for this browser session. Export the comparison to keep a copy.')
    if 'scenarios' not in st.session_state: st.session_state.scenarios=[]
    if st.button('Save current scenario',type='primary'):
        st.session_state.scenarios.append({'Material':material,'NPS':nps,'Schedule':sch,'Length (m)':length,'Pieces':result['pieces'],'Pipe tonnes':round(result['tonnes'],3),'Limit':result['limiting'],'Density':density,'Packing':packing,'Assumptions':json.dumps(values,sort_keys=True)})
    if st.session_state.scenarios:
        comparison=pd.DataFrame(st.session_state.scenarios)
        st.dataframe(comparison,width='stretch',hide_index=True)
        fig=go.Figure(go.Bar(x=[f"{i+1}. {r['Material']} {r['NPS']} / {r['Schedule']} / {r['Length (m)']} m" for i,r in enumerate(st.session_state.scenarios)],y=comparison['Pieces'],marker_color='#167D9A'))
        st.plotly_chart(style(fig,'Pieces per container by saved scenario'),width='stretch')
        st.download_button('Download comparison CSV',comparison.to_csv(index=False),'pipe_scenarios.csv','text/csv')
        if st.button('Clear saved scenarios'): st.session_state.scenarios=[];st.rerun()
    st.markdown('#### Length comparison for the selected pipe')
    lengths=[]
    for candidate_length in sorted(set([6.0,12.0,length])):
        r=calculate(pipe,candidate_length,density,Settings(**values),packing)
        lengths.append({'Length (m)':candidate_length,'Pieces':r['pieces'],'Metric tons':round(r['tonnes'],3),'Limiting factor':r['limiting']})
    st.dataframe(pd.DataFrame(lengths),hide_index=True,width='stretch')

with tabs[2]:
    st.subheader('Translate loading capacity into an order plan')
    a,b,c=st.columns(3)
    order=a.number_input('Order quantity (pieces)',min_value=1,value=1000,step=1)
    freight=b.number_input('Freight per container',min_value=0.0,value=0.0,step=100.0)
    currency=c.selectbox('Currency',['CAD','USD','EUR'])
    cost=order_cost(result,order,freight)
    if cost['containers'] is not None:
        a,b,c=st.columns(3)
        a.metric('Containers required',f"{cost['containers']:,}")
        b.metric(f'Total freight ({currency})',f"{cost['total_freight']:,.2f}")
        c.metric(f'Freight / piece ({currency})',f"{cost['freight_per_piece']:,.2f}")
        st.write(f"Last container: **{cost['last_container']:,} pieces**. Total order pipe weight: **{order*result['kg_piece']/1000:,.2f} metric tons**.")
    else: st.warning('The selected pipe cannot be loaded with the current assumptions.')
    st.caption('Enter a freight quote to enable meaningful cost estimates. Uniform full-container rates assumed, including the last partial container. No duties, insurance, taxes or currency conversion.')
    snapshot={'pipe':pipe,'length_m':length,'density_kg_m3':density,'packing':packing,'result':result,'order_pieces':order,'freight_per_container':freight,'currency':currency,'order_estimate':cost}
    st.download_button('Download calculation and assumptions (JSON)',json.dumps(snapshot,indent=2),'pipe_loading_calculation.json','application/json')

with tabs[3]:
    st.subheader('Searchable pipe reference')
    st.caption('378 chart combinations, 36 nominal sizes overall. Carbon steel through NPS 48; stainless S-schedules through NPS 30. This is chart coverage, not every commercially possible pipe or a stock list.')
    selection=st.selectbox('Catalogue material',['All','Carbon Steel','Stainless Steel'])
    frame=pd.DataFrame(rows)
    if selection!='All': frame=frame[frame.material==selection]
    query=st.text_input('Find an exact NPS or schedule',placeholder='e.g. 4, 10S or STD')
    if query: frame=frame[(frame.nps==query)|(frame.schedule==query.upper())]
    frame=frame[['material','nps','schedule','standard','od_mm','wall_mm']].copy()
    st.dataframe(frame,hide_index=True,width='stretch')
    st.download_button('Download filtered catalogue',frame.to_csv(index=False),'pipe_catalogue.csv','text/csv')

with tabs[4]:
    st.subheader('Calculation method and scope')
    st.markdown('''1. Calculate metal cross-sectional area from outside diameter and wall thickness.
2. Multiply by density and length to obtain kg per piece.
3. Compare square and staggered packing in both cross-sectional orientations, within the door-limited space after clearances.
4. Multiply cross-section positions by the number of whole pipe lengths fitting end-to-end.
5. Divide available payload by unit weight, round down, and take the smaller of geometry and weight capacity.''')
    st.latex(r'w_{kg/m}=\pi\,t\,(D-t)\,\rho/10^6')
    st.caption('D and t in mm; density in kg/m³. Regular patterns are feasible geometric candidates, not a proof of globally optimal packing. No nested pipes, mixed sizes, bundles, fittings or angled loading are modeled.')
    st.write('Default 20 mm total end clearance leaves little allowance for nominal 12 m pipes. Check actual lengths and container dimensions. Clearances, spacing and dunnage are editable planning assumptions. Density is grade dependent. A geometric pattern does not establish safe support, load distribution or securement.')
    st.markdown('''**Sources**

- [Van Leeuwen dimensional chart](https://brandportal.vanleeuwen.com/m/18aecf58d0438f63/original/Pipe-schedules-web.pdf)
- [Hapag-Lloyd 40 ft standard container](https://www.hapag-lloyd.com/en/services-information/cargo-fleet/container/40-standard.html)
- [ASME B36.10M](https://www.asme.org/codes-standards/find-codes-standards/b36-10m-welded-seamless-wrought-steel-pipe)
- [ASME B36.19M](https://www.asme.org/codes-standards/find-codes-standards/stainless-steel-pipe)

Chart data retained from the Excel assessment model. Dimensions are rounded as published in the supplier reference; confirm against the contractual standard and mill specification. Stainless B36.10 thicknesses can also be commercially available, but this catalogue currently exposes stainless S-schedules only. Source chart weight figures are not used in calculations.''')
    st.json(values)

st.caption('Planning estimate using a default 25,000 kg maximum payload. Confirm the actual equipment payload, route limits and practical loading plan before dispatch.')
