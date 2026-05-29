"""Generate 图5-3: Hybrid混合推荐流程 (水平流程, mint theme)"""
import os

drawio_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
    <diagram name="图5-3 Hybrid混合推荐流程" id="hybrid-flow">
        <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="900" pageHeight="520" background="none" math="0" shadow="0">
            <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>

                <mxCell id="title" value="图5-3 Hybrid混合推荐流程 (ItemCF召回 + NCF重排)" style="text;html=1;fontSize=14;fontColor=#1A3A3A;align=center;verticalAlign=middle;fontStyle=1;" parent="1" vertex="1">
                    <mxGeometry x="250" y="8" width="400" height="26" as="geometry"/>
                </mxCell>

                <!-- Main flow: left to right at top -->
                <!-- Node 1: Request -->
                <mxCell id="n_req" value="&lt;b&gt;用户推荐请求&lt;/b&gt;&lt;br&gt;strategy=hybrid&lt;br&gt;n=10, recall_k=100" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F5F0;strokeColor=#6DBFAB;strokeWidth=1.2;arcSize=10;fontSize=11;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="40" y="55" width="170" height="55" as="geometry"/>
                </mxCell>

                <!-- Arrow R→R1 -->
                <mxCell id="a1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#9DC0B7;strokeWidth=0.8;endSize=5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_req" target="n_itemcf" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Node 2: ItemCF Recall -->
                <mxCell id="n_itemcf" value="&lt;b&gt;ItemCF 召回阶段&lt;/b&gt;&lt;br&gt;从 movie_similarity 表查询&lt;br&gt;相似度×评分加权累加&lt;br&gt;→ 候选集 (size=recall_k)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#CCF0E8;strokeColor=#2A9D8F;strokeWidth=1.2;arcSize=10;fontSize=10;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="235" y="40" width="210" height="75" as="geometry"/>
                </mxCell>

                <!-- Arrow R1→R2 -->
                <mxCell id="a2" value="&lt;span style=&quot;font-size:9px;color:#2A9D8F&quot;&gt;候选集&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#9DC0B7;strokeWidth=0.8;endSize=5;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_itemcf" target="n_ncf" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Node 3: NCF Rerank -->
                <mxCell id="n_ncf" value="&lt;b&gt;NCF 重排阶段&lt;/b&gt;&lt;br&gt;用户/物品Embedding拼接&lt;br&gt;3层MLP非线性打分&lt;br&gt;→ 按得分降序重排" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#CCF0E8;strokeColor=#2A9D8F;strokeWidth=1.2;arcSize=10;fontSize=10;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="470" y="40" width="200" height="75" as="geometry"/>
                </mxCell>

                <!-- Arrow R2→Output -->
                <mxCell id="a3" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#9DC0B7;strokeWidth=0.8;endSize=5;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_ncf" target="n_out" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Node 4: Output -->
                <mxCell id="n_out" value="&lt;b&gt;Top-10输出&lt;/b&gt;&lt;br&gt;推荐列表 +&lt;br&gt;推荐理由&lt;br&gt;+ 推荐分数" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F5F0;strokeColor=#6DBFAB;strokeWidth=1.2;arcSize=10;fontSize=10;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="695" y="42" width="150" height="68" as="geometry"/>
                </mxCell>

                <!-- ====== FALLBACK CHAIN (below main flow) ====== -->
                <mxCell id="g_fallback" value="回退链 (Fallback Chain)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F7F5;strokeColor=#B0D0C5;strokeWidth=1.0;dashed=1;fontSize=10;fontColor=#5A7A7A;verticalAlign=top;align=left;spacingLeft=8;spacingTop=4;" parent="1" vertex="1">
                    <mxGeometry x="40" y="160" width="810" height="200" as="geometry"/>
                </mxCell>

                <!-- Check 1: NCF Ready? -->
                <mxCell id="n_check1" value="&lt;b&gt;NCF模型就绪?&lt;/b&gt;" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF4E6;strokeColor=#E9A84C;strokeWidth=1.2;fontSize=11;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="340" y="180" width="140" height="65" as="geometry"/>
                </mxCell>

                <!-- Arrow from ItemCF to Check1 -->
                <mxCell id="a4" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#9DC0B7;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_itemcf" target="n_check1" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Yes path: NCF rerank (already shown) -->
                <mxCell id="a_yes" value="&lt;span style=&quot;font-size:9px;color:#3A8E4A&quot;&gt;是 → NCF重排&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#4AAE5C;strokeWidth=0.8;endSize=5;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_check1" target="n_ncf" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="490" y="213"/>
                            <mxPoint x="490" y="77"/>
                        </Array>
                    </mxGeometry>
                </mxCell>

                <!-- No path: Fallback to ItemCF -->
                <mxCell id="n_fb1" value="&lt;b&gt;退化为 ItemCF&lt;/b&gt;&lt;br&gt;直接输出ItemCF&lt;br&gt;召回结果Top-N" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF2D6;strokeColor=#D4A040;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="340" y="270" width="140" height="55" as="geometry"/>
                </mxCell>

                <mxCell id="a_no1" value="&lt;span style=&quot;font-size:9px;color:#C85050&quot;&gt;否&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#C85050;strokeWidth=0.8;endSize=5;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_check1" target="n_fb1" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Check 2: Has ratings? -->
                <mxCell id="n_check2" value="&lt;b&gt;用户有评分记录?&lt;/b&gt;" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFF4E6;strokeColor=#E9A84C;strokeWidth=1.2;fontSize=11;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="120" y="180" width="150" height="65" as="geometry"/>
                </mxCell>

                <mxCell id="a5" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#9DC0B7;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_req" target="n_check2" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <mxCell id="n_fb2" value="&lt;b&gt;热门推荐兜底&lt;/b&gt;&lt;br&gt;返回高分热门电影&lt;br&gt;标记 cold_start=true" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FCE4E4;strokeColor=#C85050;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="120" y="270" width="150" height="52" as="geometry"/>
                </mxCell>

                <mxCell id="a_no2" value="&lt;span style=&quot;font-size:9px;color:#C85050&quot;&gt;否 (冷启动)&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#C85050;strokeWidth=0.8;endSize=5;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_check2" target="n_fb2" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <mxCell id="a_yes2" value="&lt;span style=&quot;font-size:9px;color:#3A8E4A&quot;&gt;是 → 继续&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#4AAE5C;strokeWidth=0.8;endSize=5;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_check2" target="n_itemcf" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Data source annotation -->
                <mxCell id="ann_db" value="movie_similarity表" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=6;fillColor=#D8F0EE;strokeColor=#4AADA5;strokeWidth=0.8;fontSize=9;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="235" y="130" width="90" height="35" as="geometry"/>
                </mxCell>
                <mxCell id="a_db" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#B0D0C5;strokeWidth=0.6;endSize=4;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="ann_db" target="n_itemcf" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <mxCell id="ann_ncf" value="ncf.pt" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=6;fillColor=#D8F0EE;strokeColor=#4AADA5;strokeWidth=0.8;fontSize=9;fontColor=#1A3A3A;" parent="1" vertex="1">
                    <mxGeometry x="470" y="130" width="60" height="35" as="geometry"/>
                </mxCell>
                <mxCell id="a_ncf" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#B0D0C5;strokeWidth=0.6;endSize=4;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="ann_ncf" target="n_ncf" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

            </root>
        </mxGraphModel>
    </diagram>
</mxfile>'''

path = os.path.join(os.path.dirname(__file__) or '.', 'fig5-3-hybrid-flow.drawio')
with open(path, 'w', encoding='utf-8') as f:
    f.write(drawio_xml)
print(f'Written: {path}')
