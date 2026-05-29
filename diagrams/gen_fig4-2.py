"""Generate 图4-2: 核心数据库E-R图 (ERD type, tech-blue)"""
import os

# ERD conventions from drawio-skill: shape=table containers with tableRow children
drawio_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="图4-2 核心数据库E-R图">
    <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="900" pageHeight="700" background="none" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <mxCell id="title" value="图4-2 核心数据库关系示意图" style="text;html=1;fontSize=14;fontColor=#2D3748;align=center;verticalAlign=middle;fontStyle=1;" parent="1" vertex="1">
          <mxGeometry x="300" y="8" width="300" height="26" as="geometry"/>
        </mxCell>

        <!-- TABLE: users -->
        <mxCell id="tbl_users" value="users" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#6c8ebf;fillColor=#dae8fc;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="30" y="50" width="170" height="160" as="geometry"/>
        </mxCell>
        <mxCell id="u_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_users"><mxGeometry y="30" width="170" height="22" as="geometry"/></mxCell>
        <mxCell id="u_user" value="username: VARCHAR(64) UNIQUE" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;" vertex="1" parent="tbl_users"><mxGeometry y="52" width="170" height="22" as="geometry"/></mxCell>
        <mxCell id="u_pwd" value="password_hash: VARCHAR(256)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;" vertex="1" parent="tbl_users"><mxGeometry y="74" width="170" height="22" as="geometry"/></mxCell>
        <mxCell id="u_admin" value="is_admin: BOOLEAN" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;" vertex="1" parent="tbl_users"><mxGeometry y="96" width="170" height="22" as="geometry"/></mxCell>
        <mxCell id="u_active" value="is_active: BOOLEAN" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;" vertex="1" parent="tbl_users"><mxGeometry y="118" width="170" height="22" as="geometry"/></mxCell>
        <mxCell id="u_created" value="created_at: DATETIME" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontSize=10;" vertex="1" parent="tbl_users"><mxGeometry y="140" width="170" height="20" as="geometry"/></mxCell>

        <!-- TABLE: movies -->
        <mxCell id="tbl_movies" value="movies" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#6c8ebf;fillColor=#dae8fc;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="360" y="50" width="190" height="160" as="geometry"/>
        </mxCell>
        <mxCell id="m_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_movies"><mxGeometry y="30" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="m_title" value="title: VARCHAR(255)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_movies"><mxGeometry y="52" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="m_genres" value="genres: VARCHAR(255)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_movies"><mxGeometry y="74" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="m_year" value="year: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_movies"><mxGeometry y="96" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="m_avg" value="avg_rating: FLOAT" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_movies"><mxGeometry y="118" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="m_poster" value="poster_url: VARCHAR(500)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_movies"><mxGeometry y="140" width="190" height="20" as="geometry"/></mxCell>

        <!-- TABLE: ratings -->
        <mxCell id="tbl_ratings" value="ratings" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#9673a6;fillColor=#e1d5e7;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="30" y="270" width="200" height="115" as="geometry"/>
        </mxCell>
        <mxCell id="r_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_ratings"><mxGeometry y="30" width="200" height="22" as="geometry"/></mxCell>
        <mxCell id="r_uid" value="FK user_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_ratings"><mxGeometry y="52" width="200" height="22" as="geometry"/></mxCell>
        <mxCell id="r_mid" value="FK movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_ratings"><mxGeometry y="74" width="200" height="22" as="geometry"/></mxCell>
        <mxCell id="r_rating" value="rating: FLOAT (0.5-5.0)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_ratings"><mxGeometry y="96" width="200" height="22" as="geometry"/></mxCell>
        <mxCell id="r_ts" value="timestamp: DATETIME" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_ratings"><mxGeometry y="118" width="200" height="20" as="geometry"/></mxCell>
        <!-- Unique constraints note -->
        <mxCell id="r_note" value="UNIQUE(user_id, movie_id)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=8;fontColor=#666666;fontStyle=2;" vertex="1" parent="tbl_ratings"><mxGeometry y="135" width="200" height="16" as="geometry"/></mxCell>

        <!-- TABLE: movie_similarity -->
        <mxCell id="tbl_sim" value="movie_similarity" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#82b366;fillColor=#d5e8d4;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="310" y="270" width="210" height="115" as="geometry"/>
        </mxCell>
        <mxCell id="s_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_sim"><mxGeometry y="30" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="s_mid" value="FK movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_sim"><mxGeometry y="52" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="s_smid" value="FK similar_movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_sim"><mxGeometry y="74" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="s_score" value="score: FLOAT" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_sim"><mxGeometry y="96" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="s_note" value="UNIQUE(movie_id, similar_movie_id)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=8;fontColor=#666666;fontStyle=2;" vertex="1" parent="tbl_sim"><mxGeometry y="118" width="210" height="16" as="geometry"/></mxCell>

        <!-- TABLE: reviews -->
        <mxCell id="tbl_reviews" value="reviews" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#d79b00;fillColor=#ffe6cc;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="600" y="50" width="180" height="135" as="geometry"/>
        </mxCell>
        <mxCell id="rv_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_reviews"><mxGeometry y="30" width="180" height="22" as="geometry"/></mxCell>
        <mxCell id="rv_uid" value="FK user_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_reviews"><mxGeometry y="52" width="180" height="22" as="geometry"/></mxCell>
        <mxCell id="rv_mid" value="FK movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_reviews"><mxGeometry y="74" width="180" height="22" as="geometry"/></mxCell>
        <mxCell id="rv_content" value="content: TEXT" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_reviews"><mxGeometry y="96" width="180" height="22" as="geometry"/></mxCell>
        <mxCell id="rv_status" value="status: ENUM(approved...)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_reviews"><mxGeometry y="118" width="180" height="22" as="geometry"/></mxCell>

        <!-- TABLE: user_collections -->
        <mxCell id="tbl_collections" value="user_collections" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#d79b00;fillColor=#ffe6cc;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="600" y="240" width="190" height="115" as="geometry"/>
        </mxCell>
        <mxCell id="c_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_collections"><mxGeometry y="30" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="c_uid" value="FK user_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_collections"><mxGeometry y="52" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="c_mid" value="FK movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_collections"><mxGeometry y="74" width="190" height="22" as="geometry"/></mxCell>
        <mxCell id="c_type" value="collection_type: VARCHAR(20)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_collections"><mxGeometry y="96" width="190" height="22" as="geometry"/></mxCell>

        <!-- TABLE: recommendation_feedback -->
        <mxCell id="tbl_fb" value="recommendation_feedback" style="shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#666666;fillColor=#f5f5f5;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="310" y="450" width="210" height="115" as="geometry"/>
        </mxCell>
        <mxCell id="f_id" value="PK id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_fb"><mxGeometry y="30" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="f_uid" value="FK user_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_fb"><mxGeometry y="52" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="f_mid" value="FK movie_id: INTEGER" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;fontStyle=1;" vertex="1" parent="tbl_fb"><mxGeometry y="74" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="f_fb" value="feedback: VARCHAR(16) (like/dislike)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_fb"><mxGeometry y="96" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="f_ctx" value="context: VARCHAR(64)" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;fontSize=10;" vertex="1" parent="tbl_fb"><mxGeometry y="118" width="210" height="22" as="geometry"/></mxCell>

        <!-- ===== RELATIONSHIPS ===== -->

        <!-- users 1:N ratings -->
        <mxCell id="e_u_r" value="1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#9673a6;strokeWidth=1.0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_users" target="tbl_ratings">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="115" y="230"/>
              <mxPoint x="20" y="230"/>
              <mxPoint x="20" y="328"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="lbl_ur" value="1:N (评分记录)" style="text;html=1;fontSize=8;fontColor=#718096;align=center;" parent="1" vertex="1">
          <mxGeometry x="15" y="220" width="80" height="14" as="geometry"/>
        </mxCell>

        <!-- movies 1:N ratings -->
        <mxCell id="e_m_r" value="N" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#9673a6;strokeWidth=1.0;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_movies" target="tbl_ratings">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="340" y="130"/>
              <mxPoint x="260" y="130"/>
              <mxPoint x="260" y="328"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- movies 1:N movie_similarity (via movie_id) -->
        <mxCell id="e_m_s1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#82b366;strokeWidth=1.0;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_movies" target="tbl_sim">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="455" y="230"/>
              <mxPoint x="290" y="230"/>
              <mxPoint x="290" y="328"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="lbl_ms1" value="1:N (movie_id)" style="text;html=1;fontSize=8;fontColor=#718096;align=center;" parent="1" vertex="1">
          <mxGeometry x="290" y="220" width="80" height="14" as="geometry"/>
        </mxCell>

        <!-- movies 1:N movie_similarity (via similar_movie_id - self-ref to movies) -->
        <mxCell id="e_m_s2" value="N" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#82b366;strokeWidth=1.0;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_sim" target="tbl_movies">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="415" y="255"/>
              <mxPoint x="455" y="255"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="lbl_ms2" value="1:N&#xa;(similar→movie)" style="text;html=1;fontSize=8;fontColor=#718096;align=center;" parent="1" vertex="1">
          <mxGeometry x="420" y="240" width="80" height="22" as="geometry"/>
        </mxCell>

        <!-- users 1:N reviews -->
        <mxCell id="e_u_rv" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#d79b00;strokeWidth=1.0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_users" target="tbl_reviews">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="lbl_urv" value="1:N" style="text;html=1;fontSize=8;fontColor=#718096;align=center;" parent="1" vertex="1">
          <mxGeometry x="210" y="110" width="30" height="12" as="geometry"/>
        </mxCell>

        <!-- movies 1:N reviews -->
        <mxCell id="e_m_rv" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#d79b00;strokeWidth=1.0;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_reviews" target="tbl_movies">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="690" y="40"/>
              <mxPoint x="455" y="40"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- users 1:N collections -->
        <mxCell id="e_u_c" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#d79b00;strokeWidth=1.0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_users" target="tbl_collections">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="115" y="230"/>
              <mxPoint x="580" y="230"/>
              <mxPoint x="580" y="298"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- movies 1:N collections -->
        <mxCell id="e_m_c" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERmandOne;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#d79b00;strokeWidth=1.0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="tbl_movies" target="tbl_collections">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="455" y="230"/>
              <mxPoint x="810" y="230"/>
              <mxPoint x="810" y="298"/>
            </Array>
          </mxGeometry>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

path = os.path.join(os.path.dirname(__file__) or '.', 'fig4-2-er-diagram.drawio')
with open(path, 'w', encoding='utf-8') as f:
    f.write(drawio_xml)
print(f'Written: {path}')
