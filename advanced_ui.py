"""상관분석·잠재변수 모형의 결과 시각화."""
from html import escape
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def matrix_table(matrix):
    """Excel index=False에서도 행 변수 이름을 보존한다."""
    out = matrix.copy()
    label = '행 변수'
    while label in out.columns:
        label = '_' + label
    out.insert(0,label,list(matrix.index))
    return out.reset_index(drop=True)


def correlation_heatmap(result):
    fig = px.imshow(result['correlation'],zmin=-1,zmax=1,
                    color_continuous_scale=['#506799','#f7fafb','#087f70'],
                    text_auto='.2f',aspect='auto',labels={'color':'상관계수'})
    fig.update_layout(title=result['method']+' 상관행렬',coloraxis_colorbar=dict(title='계수'))
    fig.update_xaxes(side='bottom')
    return fig


def latent_diagram(result):
    """실제 추정치로 그리는 잠재변수 관계도. 측정지표는 별도 표에서 표시."""
    names = ['X','M','Y'] if '3' in result['template'] else ['X','Y']
    positions = {'X':(0,.15),'M':(.5,.85),'Y':(1,.15)}
    is_cfa = '(CFA)' in result['template']
    connections = result['variances'] if is_cfa else result['paths']
    fig = go.Figure()
    for row in connections.to_dict('records'):
        source,target = row['설명'],row['결과']
        if source not in positions or target not in positions or source==target:
            continue
        sx,sy = positions[source]; tx,ty = positions[target]
        dx,dy = tx-sx,ty-sy
        length = np.hypot(dx,dy)
        pad = .085
        fig.add_annotation(x=tx-dx*pad/length,y=ty-dy*pad/length,
                           ax=sx+dx*pad/length,ay=sy+dy*pad/length,
                           xref='x',yref='y',axref='x',ayref='y',
                           text='',showarrow=True,arrowhead=3,startarrowhead=3,
                           arrowside='end+start' if is_cfa else 'end',arrowwidth=2,arrowcolor='#78a99b')
        fig.add_annotation(x=(sx+tx)/2,y=(sy+ty)/2 + (.10 if sy==ty else 0),
                           text=f"{row['표준화 추정치']:.3f}",showarrow=False,
                           bgcolor='#ffffff',borderpad=4,font=dict(size=13,color='#2b5c51'))
    fig.add_trace(go.Scatter(x=[positions[n][0] for n in names],y=[positions[n][1] for n in names],
                            mode='markers+text',text=[escape(n) for n in names],
                            textfont=dict(color='white',size=17),
                            marker=dict(size=54,color='#19364c',line=dict(color='#8ed8c2',width=2)),
                            hoverinfo='skip',showlegend=False))
    fig.update_xaxes(range=[-.22,1.22],visible=False,fixedrange=True)
    fig.update_yaxes(range=[-.12,1.13] if len(names)==3 else [-.3,.6],visible=False,fixedrange=True)
    fig.update_layout(title='잠재변수 관계도 · 표준화 추정치',showlegend=False)
    return fig
