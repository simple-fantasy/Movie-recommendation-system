"""Generate 图5-2: NCF模型结构图 (神经网络层, tech-blue theme)"""
import os

drawio_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
    <diagram name="图5-2 NCF模型结构" id="ncf-model">
        <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="700" pageHeight="650" background="none" math="0" shadow="0">
            <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>

                <mxCell id="title" value="图5-2 NCF模型结构 (GMF架构)" style="text;html=1;fontSize=14;fontColor=#2D3748;align=center;verticalAlign=middle;fontStyle=1;" parent="1" vertex="1">
                    <mxGeometry x="200" y="8" width="300" height="26" as="geometry"/>
                </mxCell>

                <!-- Input layer -->
                <mxCell id="g_input" value="Input Layer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#CBD5E0;strokeWidth=1.0;dashed=1;fontSize=9;fontColor=#A0AEC0;verticalAlign=top;align=left;spacingLeft=6;spacingTop=3;" parent="1" vertex="1">
                    <mxGeometry x="30" y="50" width="640" height="90" as="geometry"/>
                </mxCell>

                <mxCell id="n_user_id" value="&lt;b&gt;User ID&lt;/b&gt;&lt;br&gt;(int, 200949 users)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF2F7;strokeColor=#A0AEC0;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="100" y="68" width="150" height="40" as="geometry"/>
                </mxCell>
                <mxCell id="n_item_id" value="&lt;b&gt;Item ID&lt;/b&gt;&lt;br&gt;(int, 84432 items)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF2F7;strokeColor=#A0AEC0;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="420" y="68" width="150" height="40" as="geometry"/>
                </mxCell>

                <!-- Embedding layer -->
                <mxCell id="g_emb" value="Embedding Layer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#CBD5E0;strokeWidth=1.0;dashed=1;fontSize=9;fontColor=#A0AEC0;verticalAlign=top;align=left;spacingLeft=6;spacingTop=3;" parent="1" vertex="1">
                    <mxGeometry x="30" y="155" width="640" height="90" as="geometry"/>
                </mxCell>

                <mxCell id="n_u_emb" value="&lt;b&gt;User Embedding&lt;/b&gt;&lt;br&gt;nn.Embedding(N, 32)&lt;br&gt;→ [batch, 32]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="100" y="173" width="160" height="50" as="geometry"/>
                </mxCell>
                <mxCell id="n_i_emb" value="&lt;b&gt;Item Embedding&lt;/b&gt;&lt;br&gt;nn.Embedding(M, 32)&lt;br&gt;→ [batch, 32]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="420" y="173" width="160" height="50" as="geometry"/>
                </mxCell>

                <!-- Arrows: ID→Emb -->
                <mxCell id="a_id2emb1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#5B8DEF;strokeWidth=1.0;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_user_id" target="n_u_emb" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>
                <mxCell id="a_id2emb2" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#5B8DEF;strokeWidth=1.0;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_item_id" target="n_i_emb" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Concat -->
                <mxCell id="n_concat" value="&lt;b&gt;Concatenate&lt;/b&gt;&lt;br&gt;torch.cat([u, i], dim=-1)&lt;br&gt;→ [batch, 64]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4F9;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="220" y="258" width="240" height="48" as="geometry"/>
                </mxCell>

                <mxCell id="a_emb2cat1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#5B8DEF;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_u_emb" target="n_concat" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="180" y="238"/>
                            <mxPoint x="180" y="282"/>
                        </Array>
                    </mxGeometry>
                </mxCell>
                <mxCell id="a_emb2cat2" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#5B8DEF;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_i_emb" target="n_concat" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="500" y="238"/>
                            <mxPoint x="500" y="282"/>
                        </Array>
                    </mxGeometry>
                </mxCell>

                <!-- MLP Layer -->
                <mxCell id="g_mlp" value="MLP Interaction Layers" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#CBD5E0;strokeWidth=1.0;dashed=1;fontSize=9;fontColor=#A0AEC0;verticalAlign=top;align=left;spacingLeft=6;spacingTop=3;" parent="1" vertex="1">
                    <mxGeometry x="30" y="320" width="640" height="160" as="geometry"/>
                </mxCell>

                <mxCell id="n_fc1" value="&lt;b&gt;Linear(64, 128)&lt;/b&gt;&lt;br&gt;+ ReLU" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="240" y="340" width="200" height="42" as="geometry"/>
                </mxCell>
                <mxCell id="n_fc2" value="&lt;b&gt;Linear(128, 64)&lt;/b&gt;&lt;br&gt;+ ReLU" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="240" y="395" width="200" height="42" as="geometry"/>
                </mxCell>
                <mxCell id="n_fc3" value="&lt;b&gt;Linear(64, 1)&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF0E5;strokeColor=#E8A87C;strokeWidth=1.0;arcSize=10;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="270" y="448" width="140" height="36" as="geometry"/>
                </mxCell>

                <mxCell id="a_mlp1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_concat" target="n_fc1" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>
                <mxCell id="a_mlp2" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_fc1" target="n_fc2" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>
                <mxCell id="a_mlp3" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_fc2" target="n_fc3" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Sigmoid output -->
                <mxCell id="n_sigmoid" value="&lt;b&gt;Sigmoid&lt;/b&gt;&lt;br&gt;σ(x) = 1/(1+e⁻ˣ)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E6F5EC;strokeColor=#5BA87C;strokeWidth=1.2;arcSize=10;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="250" y="505" width="180" height="42" as="geometry"/>
                </mxCell>
                <mxCell id="a_sig" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_fc3" target="n_sigmoid" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Output score -->
                <mxCell id="n_score" value="&lt;b&gt;Preference Score ŷ ∈ [0,1]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4D8;strokeColor=#8AAE8C;strokeWidth=1.2;arcSize=10;fontSize=11;fontColor=#2D3748;fontStyle=1;" parent="1" vertex="1">
                    <mxGeometry x="200" y="565" width="280" height="36" as="geometry"/>
                </mxCell>
                <mxCell id="a_out" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#5BA87C;strokeWidth=1.0;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_sigmoid" target="n_score" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Loss annotation -->
                <mxCell id="ann_loss" value="&lt;b&gt;Training&lt;/b&gt;&lt;br&gt;BCEWithLogitsLoss&lt;br&gt;Adam (lr=1e-3)&lt;br&gt;Early Stopping (patience=3)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDE8F5;strokeColor=#8B7EC4;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="40" y="510" width="175" height="55" as="geometry"/>
                </mxCell>
                <mxCell id="a_loss" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#8B7EC4;strokeWidth=0.8;endSize=5;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="ann_loss" target="n_score" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="130" y="510"/>
                            <mxPoint x="130" y="583"/>
                        </Array>
                    </mxGeometry>
                </mxCell>

            </root>
        </mxGraphModel>
    </diagram>
</mxfile>'''

path = os.path.join(os.path.dirname(__file__) or '.', 'fig5-2-ncf-model.drawio')
with open(path, 'w', encoding='utf-8') as f:
    f.write(drawio_xml)
print(f'Written: {path}')
