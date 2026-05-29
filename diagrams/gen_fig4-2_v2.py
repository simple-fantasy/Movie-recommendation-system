"""
图4-2: 核心数据库E-R图 v2
IE (Information Engineering) 记法 — PK/FK分隔线, 基数标注 1/N
7个核心实体 + 文字注释其余12张表
"""
import os, subprocess, sys

XML = r'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="图4-2 核心数据库E-R图" id="er">
    <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1"
      connect="1" arrows="1" fold="1" page="0" pageScale="1"
      pageWidth="1100" pageHeight="750" background="none" math="0" shadow="0">
      <root>
        <mxCell id="0"/><mxCell id="1" parent="0"/>

        <!-- Title -->
        <mxCell id="t" value="图4-2 核心数据库关系示意图 (E-R Diagram)" style="text;html=1;fontSize=15;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="330" y="6" width="440" height="26" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: users ═══════════ -->
        <mxCell id="e_users" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="40" y="50" width="185" height="155" as="geometry"/></mxCell>
        <mxCell id="eu_hdr" value="&lt;b&gt;users&lt;/b&gt;" style="text;html=1;fontSize=12;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="52" width="185" height="22" as="geometry"/></mxCell>
        <mxCell id="eu_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="40" y="76" width="185" height="4" as="geometry"/></mxCell>
        <mxCell id="eu_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="80" width="185" height="18" as="geometry"/></mxCell>
        <mxCell id="eu_name" value="username &amp;nbsp;VARCHAR(64)&amp;nbsp;U" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="98" width="185" height="18" as="geometry"/></mxCell>
        <mxCell id="eu_pwd" value="password_hash &amp;nbsp;VARCHAR(256)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="116" width="185" height="16" as="geometry"/></mxCell>
        <mxCell id="eu_adm" value="is_admin &amp;nbsp;BOOL" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="132" width="185" height="16" as="geometry"/></mxCell>
        <mxCell id="eu_act" value="is_active &amp;nbsp;BOOL" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="148" width="185" height="16" as="geometry"/></mxCell>
        <mxCell id="eu_ca" value="created_at &amp;nbsp;DATETIME" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="164" width="185" height="16" as="geometry"/></mxCell>
        <mxCell id="eu_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="40" y="182" width="185" height="4" as="geometry"/></mxCell>
        <mxCell id="eu_idx" value="INDEX(username, created_at)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="40" y="186" width="185" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: movies ═══════════ -->
        <mxCell id="e_movies" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="410" y="50" width="200" height="170" as="geometry"/></mxCell>
        <mxCell id="em_hdr" value="&lt;b&gt;movies&lt;/b&gt;" style="text;html=1;fontSize=12;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="410" y="52" width="200" height="22" as="geometry"/></mxCell>
        <mxCell id="em_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="410" y="76" width="200" height="4" as="geometry"/></mxCell>
        <mxCell id="em_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="80" width="200" height="18" as="geometry"/></mxCell>
        <mxCell id="em_title" value="title &amp;nbsp;VARCHAR(255)&amp;nbsp;INDEX" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="98" width="200" height="18" as="geometry"/></mxCell>
        <mxCell id="em_yr" value="year &amp;nbsp;INT&amp;nbsp;&amp;nbsp;INDEX" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="116" width="200" height="16" as="geometry"/></mxCell>
        <mxCell id="em_genres" value="genres &amp;nbsp;VARCHAR(255)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="132" width="200" height="16" as="geometry"/></mxCell>
        <mxCell id="em_avg" value="avg_rating &amp;nbsp;FLOAT" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="148" width="200" height="16" as="geometry"/></mxCell>
        <mxCell id="em_dir" value="director &amp;nbsp;VARCHAR(255)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="164" width="200" height="16" as="geometry"/></mxCell>
        <mxCell id="em_poster" value="poster_url &amp;nbsp;VARCHAR(500)" style="text;html=1;fontSize=9;fontColor=#AAAAAA;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="180" width="200" height="16" as="geometry"/></mxCell>
        <mxCell id="em_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#6C8EBF;" vertex="1" parent="1">
          <mxGeometry x="410" y="198" width="200" height="4" as="geometry"/></mxCell>
        <mxCell id="em_idx" value="INDEX(title, year, avg_rating)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="410" y="202" width="200" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: ratings ═══════════ -->
        <mxCell id="e_ratings" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#E1D5E7;strokeColor=#9673A6;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="230" y="280" width="195" height="130" as="geometry"/></mxCell>
        <mxCell id="er_hdr" value="&lt;b&gt;ratings&lt;/b&gt;" style="text;html=1;fontSize=12;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="230" y="282" width="195" height="22" as="geometry"/></mxCell>
        <mxCell id="er_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#9673A6;" vertex="1" parent="1">
          <mxGeometry x="230" y="306" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="er_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="230" y="310" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="er_fk1" value="&lt;u&gt;user_id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;FK→users" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="230" y="328" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="er_fk2" value="&lt;u&gt;movie_id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="230" y="346" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="er_r" value="rating &amp;nbsp;FLOAT&amp;nbsp;(0.5-5.0)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="230" y="364" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="er_ts" value="timestamp &amp;nbsp;DATETIME" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="230" y="380" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="er_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#9673A6;" vertex="1" parent="1">
          <mxGeometry x="230" y="398" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="er_uq" value="UNIQUE(user_id, movie_id)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="230" y="402" width="195" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: movie_similarity ═══════════ -->
        <mxCell id="e_sim" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#D5E8D4;strokeColor=#82B366;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="40" y="280" width="185" height="115" as="geometry"/></mxCell>
        <mxCell id="es_hdr" value="&lt;b&gt;movie_similarity&lt;/b&gt;" style="text;html=1;fontSize=11;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="282" width="185" height="22" as="geometry"/></mxCell>
        <mxCell id="es_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#82B366;" vertex="1" parent="1">
          <mxGeometry x="40" y="306" width="185" height="4" as="geometry"/></mxCell>
        <mxCell id="es_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="310" width="185" height="18" as="geometry"/></mxCell>
        <mxCell id="es_fk1" value="&lt;u&gt;movie_id&lt;/u&gt; &amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="328" width="185" height="18" as="geometry"/></mxCell>
        <mxCell id="es_fk2" value="&lt;u&gt;similar_movie_id&lt;/u&gt; &amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="346" width="185" height="18" as="geometry"/></mxCell>
        <mxCell id="es_sc" value="score &amp;nbsp;FLOAT" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="364" width="185" height="16" as="geometry"/></mxCell>
        <mxCell id="es_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#82B366;" vertex="1" parent="1">
          <mxGeometry x="40" y="382" width="185" height="4" as="geometry"/></mxCell>
        <mxCell id="es_uq" value="UNIQUE(movie_id, similar_movie_id)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="40" y="386" width="185" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: reviews ═══════════ -->
        <mxCell id="e_rev" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFE6CC;strokeColor=#D79B00;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="760" y="50" width="195" height="155" as="geometry"/></mxCell>
        <mxCell id="ev_hdr" value="&lt;b&gt;reviews&lt;/b&gt;" style="text;html=1;fontSize=12;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="760" y="52" width="195" height="22" as="geometry"/></mxCell>
        <mxCell id="ev_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#D79B00;" vertex="1" parent="1">
          <mxGeometry x="760" y="76" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="ev_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="80" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ev_uid" value="&lt;u&gt;user_id&lt;/u&gt; &amp;nbsp;FK→users" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="98" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ev_mid" value="&lt;u&gt;movie_id&lt;/u&gt; &amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="116" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ev_ct" value="content &amp;nbsp;TEXT" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="134" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="ev_st" value="status &amp;nbsp;ENUM(approved…)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="150" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="ev_lc" value="likes_count &amp;nbsp;INT" style="text;html=1;fontSize=9;fontColor=#AAAAAA;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="166" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="ev_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#D79B00;" vertex="1" parent="1">
          <mxGeometry x="760" y="184" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="ev_idx" value="INDEX(user_id, movie_id, created_at)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="760" y="188" width="195" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: user_collections ═══════════ -->
        <mxCell id="e_col" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFE6CC;strokeColor=#D79B00;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="760" y="280" width="195" height="115" as="geometry"/></mxCell>
        <mxCell id="ec_hdr" value="&lt;b&gt;user_collections&lt;/b&gt;" style="text;html=1;fontSize=11;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="760" y="282" width="195" height="22" as="geometry"/></mxCell>
        <mxCell id="ec_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#D79B00;" vertex="1" parent="1">
          <mxGeometry x="760" y="306" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="ec_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="310" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ec_uid" value="&lt;u&gt;user_id&lt;/u&gt; &amp;nbsp;FK→users" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="328" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ec_mid" value="&lt;u&gt;movie_id&lt;/u&gt; &amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="346" width="195" height="18" as="geometry"/></mxCell>
        <mxCell id="ec_type" value="collection_type &amp;nbsp;VARCHAR(20)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="760" y="364" width="195" height="16" as="geometry"/></mxCell>
        <mxCell id="ec_sep2" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#D79B00;" vertex="1" parent="1">
          <mxGeometry x="760" y="382" width="195" height="4" as="geometry"/></mxCell>
        <mxCell id="ec_uq" value="UNIQUE(user_id, movie_id, type)" style="text;html=1;fontSize=8;fontColor=#888888;align=left;spacingLeft=6;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="760" y="386" width="195" height="14" as="geometry"/></mxCell>

        <!-- ═══════════ ENTITY: recommendation_feedback ═══════════ -->
        <mxCell id="e_fb" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;strokeWidth=1.6;" vertex="1" parent="1">
          <mxGeometry x="410" y="280" width="210" height="115" as="geometry"/></mxCell>
        <mxCell id="ef_hdr" value="&lt;b&gt;recommendation_feedback&lt;/b&gt;" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=center;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="410" y="282" width="210" height="22" as="geometry"/></mxCell>
        <mxCell id="ef_sep" value="" style="line;strokeWidth=1;fillColor=none;strokeColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="410" y="306" width="210" height="4" as="geometry"/></mxCell>
        <mxCell id="ef_pk" value="&lt;u&gt;id&lt;/u&gt; &amp;nbsp;INT&amp;nbsp;&amp;nbsp;&amp;nbsp;PK" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="310" width="210" height="18" as="geometry"/></mxCell>
        <mxCell id="ef_uid" value="&lt;u&gt;user_id&lt;/u&gt; &amp;nbsp;FK→users" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="328" width="210" height="18" as="geometry"/></mxCell>
        <mxCell id="ef_mid" value="&lt;u&gt;movie_id&lt;/u&gt; &amp;nbsp;FK→movies" style="text;html=1;fontSize=10;fontColor=#1A1A1A;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="346" width="210" height="18" as="geometry"/></mxCell>
        <mxCell id="ef_fb" value="feedback &amp;nbsp;VARCHAR(16)&amp;nbsp;(like/dislike)" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="364" width="210" height="16" as="geometry"/></mxCell>
        <mxCell id="ef_ctx" value="context &amp;nbsp;VARCHAR(64)" style="text;html=1;fontSize=9;fontColor=#AAAAAA;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="410" y="380" width="210" height="16" as="geometry"/></mxCell>

        <!-- ═══════════ RELATIONSHIPS ═══════════ -->

        <!-- users 1──N ratings (via user_id) -->
        <mxCell id="r1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#9673A6;strokeWidth=1.2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_users" target="e_ratings">
          <mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="l1" value="&lt;font style=&quot;font-size:9;color:#9673A6&quot;&gt;1&lt;/font&gt;" style="text;html=1;fontSize=9;align=center;" vertex="1" parent="1">
          <mxGeometry x="218" y="108" width="20" height="14" as="geometry"/></mxCell>

        <!-- movies 1──N ratings (via movie_id) -->
        <mxCell id="r2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#9673A6;strokeWidth=1.2;exitX=0;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_movies" target="e_ratings">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="410" y="240"/><mxPoint x="330" y="240"/></Array></mxGeometry></mxCell>
        <mxCell id="l2" value="&lt;font style=&quot;font-size:9;color:#9673A6&quot;&gt;N&lt;/font&gt;" style="text;html=1;fontSize=9;align=center;" vertex="1" parent="1">
          <mxGeometry x="375" y="283" width="20" height="14" as="geometry"/></mxCell>

        <!-- users 1──N reviews -->
        <mxCell id="r3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#D79B00;strokeWidth=1.2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_users" target="e_rev">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="236" y="128"/><mxPoint x="236" y="50"/><mxPoint x="760" y="128"/></Array></mxGeometry></mxCell>
        <mxCell id="l3" value="&lt;font style=&quot;font-size:9;color:#D79B00&quot;&gt;1&lt;/font&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;font style=&quot;font-size:9;color:#D79B00&quot;&gt;N&lt;/font&gt;" style="text;html=1;fontSize=9;align=center;" vertex="1" parent="1">
          <mxGeometry x="480" y="55" width="260" height="14" as="geometry"/></mxCell>

        <!-- movies 1──N reviews -->
        <mxCell id="r4" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#D79B00;strokeWidth=1.2;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_movies" target="e_rev">
          <mxGeometry relative="1" as="geometry"/></mxCell>

        <!-- users 1──N collections -->
        <mxCell id="r5" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#D79B00;strokeWidth=1.2;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_users" target="e_col">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="133" y="230"/><mxPoint x="750" y="230"/><mxPoint x="750" y="338"/></Array></mxGeometry></mxCell>

        <!-- movies 1──N collections -->
        <mxCell id="r6" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#D79B00;strokeWidth=1.2;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_movies" target="e_col">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="510" y="240"/><mxPoint x="970" y="240"/><mxPoint x="970" y="338"/></Array></mxGeometry></mxCell>

        <!-- users 1──N feedback -->
        <mxCell id="r7" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#666666;strokeWidth=1.2;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_users" target="e_fb">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="133" y="230"/><mxPoint x="515" y="230"/></Array></mxGeometry></mxCell>

        <!-- movies 1──N feedback -->
        <mxCell id="r8" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#666666;strokeWidth=1.2;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_movies" target="e_fb">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="510" y="240"/><mxPoint x="640" y="240"/><mxPoint x="640" y="338"/></Array></mxGeometry></mxCell>

        <!-- movies 1──N movie_similarity (movie_id) -->
        <mxCell id="r9" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#82B366;strokeWidth=1.2;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_movies" target="e_sim">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="370" y="135"/><mxPoint x="370" y="338"/></Array></mxGeometry></mxCell>
        <mxCell id="l9" value="&lt;font style=&quot;font-size:9;color:#82B366&quot;&gt;1&lt;/font&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;font style=&quot;font-size:9;color:#82B366&quot;&gt;N&lt;/font&gt;" style="text;html=1;fontSize=9;align=center;" vertex="1" parent="1">
          <mxGeometry x="210" y="283" width="140" height="14" as="geometry"/></mxCell>

        <!-- movies 1──N movie_similarity (similar_movie_id — self-ref) -->
        <mxCell id="r10" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=ERone;startArrow=ERmany;endFill=0;startFill=0;strokeColor=#82B366;strokeWidth=1.2;exitX=0;exitY=0;exitDx=0;exitDy=0;entryX=0;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="e_sim" target="e_movies">
          <mxGeometry relative="1" as="geometry">
            <Array as="points"><mxPoint x="30" y="338"/><mxPoint x="30" y="20"/><mxPoint x="400" y="20"/></Array></mxGeometry></mxCell>
        <mxCell id="l10" value="&lt;font style=&quot;font-size:8;color:#82B366&quot;&gt;1&lt;/font&gt;&amp;nbsp;(自关联)&amp;nbsp;&lt;font style=&quot;font-size:8;color:#82B366&quot;&gt;N&lt;/font&gt;" style="text;html=1;fontSize=8;align=center;" vertex="1" parent="1">
          <mxGeometry x="180" y="16" width="140" height="14" as="geometry"/></mxCell>

        <!-- Annotation: Other tables -->
        <mxCell id="note" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;strokeWidth=1.0;dashed=1;" vertex="1" parent="1">
          <mxGeometry x="440" y="430" width="600" height="70" as="geometry"/></mxCell>
        <mxCell id="note_txt" value="&lt;b&gt;附加支撑表 (12张)&lt;/b&gt;&lt;br&gt;review_likes (评论点赞)  |  watch_links (观影链接)  |  user_behaviors (行为日志)&lt;br&gt;user_profiles (用户画像: 12维特征)  |  alembic_version (迁移版本) 等" style="text;html=1;fontSize=9;fontColor=#666666;align=center;spacingTop=4;" vertex="1" parent="1">
          <mxGeometry x="450" y="438" width="580" height="56" as="geometry"/></mxCell>

        <!-- Legend -->
        <mxCell id="leg_box" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#CCCCCC;strokeWidth=1.0;" vertex="1" parent="1">
          <mxGeometry x="40" y="430" width="380" height="65" as="geometry"/></mxCell>
        <mxCell id="leg_t" value="&lt;b&gt;图例&lt;/b&gt;&amp;nbsp; ── 实线 = N:1关系&amp;nbsp; &amp;nbsp;- - 虚线 = 弱关联&amp;nbsp; &amp;nbsp;&lt;u&gt;下划线&lt;/u&gt; = FK外键" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;spacingTop=4;" vertex="1" parent="1">
          <mxGeometry x="50" y="438" width="360" height="50" as="geometry"/></mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

script_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(script_dir, 'fig4-2-er-diagram.drawio')
with open(path, 'w', encoding='utf-8') as f:
    f.write(XML)
print(f'Written: {path}')
