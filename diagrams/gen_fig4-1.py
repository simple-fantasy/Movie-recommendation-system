"""Generate 图4-1: 系统总体架构图"""
import os

drawio_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
    <diagram name="图4-1 系统总体架构图" id="arch">
        <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="920" pageHeight="780" background="none" math="0" shadow="0">
            <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>

                <mxCell id="title" value="图4-1 系统总体架构图" style="text;html=1;fontSize=16;fontColor=#2D3748;align=center;verticalAlign=middle;fontStyle=1;" parent="1" vertex="1">
                    <mxGeometry x="210" y="10" width="500" height="30" as="geometry"/>
                </mxCell>

                <!-- LAYER 1: 展示层 -->
                <mxCell id="g_pres" value="展示层 (Presentation)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FF;strokeColor=#A5B4FC;strokeWidth=1.0;dashed=1;fontSize=11;fontColor=#6366F1;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;" parent="1" vertex="1">
                    <mxGeometry x="30" y="55" width="520" height="170" as="geometry"/>
                </mxCell>

                <mxCell id="n_jinja" value="&lt;b&gt;Jinja2模板引擎&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=12;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="50" y="80" width="115" height="36" as="geometry"/>
                </mxCell>
                <mxCell id="n_vue" value="&lt;b&gt;Vue.js 3&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=12;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="175" y="80" width="115" height="36" as="geometry"/>
                </mxCell>
                <mxCell id="n_bs" value="&lt;b&gt;Bootstrap 5&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=12;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="300" y="80" width="115" height="36" as="geometry"/>
                </mxCell>
                <mxCell id="n_echarts" value="&lt;b&gt;ECharts 5.4&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=12;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="425" y="80" width="115" height="36" as="geometry"/>
                </mxCell>

                <mxCell id="l_pres_note" value="Server-side渲染 + CDN响应式组件 + Dark Theme + 数据可视化" style="text;html=1;fontSize=9;fontColor=#718096;align=center;" parent="1" vertex="1">
                    <mxGeometry x="50" y="130" width="490" height="16" as="geometry"/>
                </mxCell>

                <mxCell id="n_pages" value="&lt;b&gt;页面&lt;/b&gt;: 门户 登录 推荐 详情 收藏 看板 画像 管理后台" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E0;strokeWidth=0.8;arcSize=6;fontSize=9;fontColor=#4A5568;" parent="1" vertex="1">
                    <mxGeometry x="50" y="158" width="490" height="28" as="geometry"/>
                </mxCell>

                <!-- LAYER 2: 服务层 -->
                <mxCell id="g_svc" value="服务层 / API层 (Service)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF5FF;strokeColor=#93C5FD;strokeWidth=1.0;dashed=1;fontSize=11;fontColor=#3B82F6;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;" parent="1" vertex="1">
                    <mxGeometry x="30" y="240" width="520" height="270" as="geometry"/>
                </mxCell>

                <mxCell id="n_flask" value="&lt;b&gt;Flask App Factory&lt;/b&gt;&lt;br&gt;create_app() + Blueprint + 中间件" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4F9;strokeColor=#5B8DEF;strokeWidth=1.2;arcSize=10;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="160" y="268" width="240" height="44" as="geometry"/>
                </mxCell>

                <mxCell id="n_auth" value="&lt;b&gt;认证&lt;/b&gt;&lt;br&gt;Flask-Login&lt;br&gt;密码哈希" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="50" y="328" width="100" height="52" as="geometry"/>
                </mxCell>
                <mxCell id="n_rec" value="&lt;b&gt;推荐引擎&lt;/b&gt;&lt;br&gt;ItemCF→NCF&lt;br&gt;→Hybrid" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF0E5;strokeColor=#E8A87C;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="160" y="328" width="115" height="52" as="geometry"/>
                </mxCell>
                <mxCell id="n_profile" value="&lt;b&gt;用户画像&lt;/b&gt;&lt;br&gt;ProfileService&lt;br&gt;12维特征" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="285" y="328" width="110" height="52" as="geometry"/>
                </mxCell>
                <mxCell id="n_behavior" value="&lt;b&gt;行为追踪&lt;/b&gt;&lt;br&gt;异步非阻塞&lt;br&gt;线程池" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="405" y="328" width="110" height="52" as="geometry"/>
                </mxCell>

                <mxCell id="n_cache" value="&lt;b&gt;缓存&lt;/b&gt;&lt;br&gt;FileSystemCache" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF2F7;strokeColor=#A0AEC0;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="50" y="395" width="110" height="40" as="geometry"/>
                </mxCell>
                <mxCell id="n_rate" value="&lt;b&gt;限流&lt;/b&gt;&lt;br&gt;滑动窗口" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF2F7;strokeColor=#A0AEC0;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="170" y="395" width="90" height="40" as="geometry"/>
                </mxCell>
                <mxCell id="n_config" value="&lt;b&gt;配置&lt;/b&gt;&lt;br&gt;Pydantic Settings" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF2F7;strokeColor=#A0AEC0;strokeWidth=1.0;arcSize=8;fontSize=9;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="270" y="395" width="115" height="40" as="geometry"/>
                </mxCell>
                <mxCell id="n_api_count" value="&lt;b&gt;~70 REST API&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E0;strokeWidth=0.8;arcSize=6;fontSize=9;fontColor=#4A5568;" parent="1" vertex="1">
                    <mxGeometry x="395" y="395" width="120" height="40" as="geometry"/>
                </mxCell>

                <mxCell id="l_svc_note" value="Blueprint路由 + 装饰器认证 + 全局中间件 (日志/限流/CORS)" style="text;html=1;fontSize=9;fontColor=#718096;align=center;" parent="1" vertex="1">
                    <mxGeometry x="50" y="450" width="490" height="16" as="geometry"/>
                </mxCell>

                <!-- LAYER 3: 数据层 -->
                <mxCell id="g_data" value="数据层 (Data)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#86EFAC;strokeWidth=1.0;dashed=1;fontSize=11;fontColor=#22C55E;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;" parent="1" vertex="1">
                    <mxGeometry x="30" y="525" width="520" height="145" as="geometry"/>
                </mxCell>

                <mxCell id="n_db" value="&lt;b&gt;MySQL / SQLite&lt;/b&gt;&lt;br&gt;SQLAlchemy ORM&lt;br&gt;11个模型 19张表" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=8;fillColor=#E8F4F2;strokeColor=#5BA8A0;strokeWidth=1.2;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="55" y="552" width="145" height="55" as="geometry"/>
                </mxCell>
                <mxCell id="n_sim" value="&lt;b&gt;电影相似度表&lt;/b&gt;&lt;br&gt;ItemCF TopK预计算" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=8;fillColor=#E8F4F2;strokeColor=#5BA8A0;strokeWidth=1.2;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="218" y="552" width="145" height="55" as="geometry"/>
                </mxCell>
                <mxCell id="n_model" value="&lt;b&gt;NCF模型文件&lt;/b&gt;&lt;br&gt;ncf.pt + ncf_meta.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F4F2;strokeColor=#5BA8A0;strokeWidth=1.0;arcSize=8;fontSize=10;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="380" y="552" width="145" height="55" as="geometry"/>
                </mxCell>

                <mxCell id="l_data_note" value="连接池 (pool_pre_ping) + 事务管理 + 唯一约束 + 复合索引" style="text;html=1;fontSize=9;fontColor=#718096;align=center;" parent="1" vertex="1">
                    <mxGeometry x="50" y="622" width="490" height="16" as="geometry"/>
                </mxCell>

                <!-- RIGHT SIDE: 离线训练管线 -->
                <mxCell id="g_train" value="离线训练管线 (Offline Pipeline)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF7ED;strokeColor=#FDBA74;strokeWidth=1.0;dashed=1;fontSize=11;fontColor=#EA580C;verticalAlign=top;align=left;spacingLeft=8;spacingTop=6;" parent="1" vertex="1">
                    <mxGeometry x="560" y="55" width="320" height="600" as="geometry"/>
                </mxCell>

                <mxCell id="n_import" value="&lt;b&gt;1. 数据导入&lt;/b&gt;&lt;br&gt;import_fast.py&lt;br&gt;MovieLens 32M + TMDB补充" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F0FE;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="580" y="75" width="280" height="55" as="geometry"/>
                </mxCell>
                <mxCell id="n_itemcf_t" value="&lt;b&gt;2. ItemCF训练&lt;/b&gt;&lt;br&gt;scikit-learn NearestNeighbors&lt;br&gt;余弦相似度 + TopK截断&lt;br&gt;→ movie_similarity表" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4F9;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="580" y="155" width="280" height="65" as="geometry"/>
                </mxCell>
                <mxCell id="n_ncf_t" value="&lt;b&gt;3. NCF训练&lt;/b&gt;&lt;br&gt;PyTorch MLP架构 (Embedding+MLP)&lt;br&gt;BCE Loss + 负采样 + 早停(patience=3)&lt;br&gt;→ ncf.pt + ncf_meta.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4F9;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="580" y="245" width="280" height="68" as="geometry"/>
                </mxCell>
                <mxCell id="n_eval_t" value="&lt;b&gt;4. 离线评估&lt;/b&gt;&lt;br&gt;5项指标: P@K R@K MAP@K NDCG@K MRR@K&lt;br&gt;Coverage + Popularity Bias&lt;br&gt;消融实验 → evaluation_results.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#D6E4F9;strokeColor=#5B8DEF;strokeWidth=1.0;arcSize=8;fontSize=11;fontColor=#2D3748;" parent="1" vertex="1">
                    <mxGeometry x="580" y="338" width="280" height="68" as="geometry"/>
                </mxCell>

                <!-- Vertical arrows: offline pipeline -->
                <mxCell id="a_t1" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_import" target="n_itemcf_t" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>
                <mxCell id="a_t2" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_itemcf_t" target="n_ncf_t" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>
                <mxCell id="a_t3" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#93C5FD;strokeWidth=0.8;endSize=5;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" parent="1" source="n_ncf_t" target="n_eval_t" edge="1">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>

                <!-- Dashed cross-arrows: training → data -->
                <mxCell id="a_train2sim" value="&lt;span style=&quot;font-size:8px;color:#EA580C&quot;&gt;写入相似度&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#FDBA74;strokeWidth=0.8;endSize=5;dashed=1;html=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_itemcf_t" target="n_sim" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="540" y="188"/>
                            <mxPoint x="540" y="580"/>
                        </Array>
                    </mxGeometry>
                </mxCell>

                <mxCell id="a_train2model" value="&lt;span style=&quot;font-size:8px;color:#EA580C&quot;&gt;保存权重&lt;/span&gt;" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;strokeColor=#FDBA74;strokeWidth=0.8;endSize=5;dashed=1;html=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="n_ncf_t" target="n_model" edge="1">
                    <mxGeometry relative="1" as="geometry">
                        <Array as="points">
                            <mxPoint x="540" y="279"/>
                            <mxPoint x="540" y="580"/>
                        </Array>
                    </mxGeometry>
                </mxCell>

            </root>
        </mxGraphModel>
    </diagram>
</mxfile>'''

path = os.path.join(os.path.dirname(__file__) or '.', 'fig4-1-architecture.drawio')
with open(path, 'w', encoding='utf-8') as f:
    f.write(drawio_xml)
print(f'Written: {path}')
