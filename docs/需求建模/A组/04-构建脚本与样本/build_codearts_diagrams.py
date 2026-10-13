"""Build CodeArts model-project ZIPs for the assignment-2 diagrams.

The ZIP layout is an internal export format, not a public schema.  Every
generated project keeps the metadata, record shapes and canvas object shapes of
the user's own export (test1_master_20261012184125.zip) so that CodeArts sees
the same structure it produced.  Shapes are cloned from real objects of that
export wherever one exists:

  State / Initial(shape=startState) / transition   -> from the 状态机图 canvas
  Actor / Boundary / UseCase / connector           -> from the yl 用例图 canvas
  Decision(shape=rhombus) / Final(shape=endState)  -> mxGraph core / draw.io
                                                      UML names, see the notes in
                                                      the delivery README.

Nothing here is verified by an actual CodeArts import; the ZIP is a starting
point to import, check and then export as PNG.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
# The script lives in '04-构建脚本与样本/'; its sample stays beside it and the
# generated ZIPs are written to the figure folder of 'A组/'.
A_GROUP = HERE.parent
SOURCE = HERE / 'test1_master_20261012184125.zip'
OUT_DIR = A_GROUP / '02-模型图' / 'CodeArts待导入ZIP'
OLD_PREFIX = 'test1_master_20261012184125/'

# Diagram type UUIDs taken from 1_meta/3_view_types.json of the sample export.
UML_PARENT = 'ff1ee18c-ac06-11e8-9e12-0242ac117104'
T_UML_USECASE = 'ff1ee4d6-ac06-11e8-9e12-0242ac117104'
T_UML_ACTIVITY = 'ff1ee59d-ac06-11e8-9e12-0242ac117104'
T_UML_STATEMACHINE = 'ff1ee701-ac06-11e8-9e12-0242ac117104'

# Canvas styles.  The first two are copied verbatim from the sample canvases.
S_STATE = ('container=1;html=1;arcSize=4;verticalAlign=top;disableFoldingImage=1;'
           'strokeColor=#808080;fillColor=#FFE6CC;rounded=1;shadow=1;fontFamily=Helvetica;'
           'fontSize=12;fontColor=#333333;whiteSpace=wrap;gradientColor=#FFFFFF;'
           'gradientDirection=east')
S_INITIAL = ('container=0;html=1;arcSize=4;verticalAlign=middle;disableFoldingImage=1;'
             'strokeColor=#4D4D4D;fillColor=#4D4D4D;rounded=1;shadow=0;fontFamily=Helvetica;'
             'fontSize=12;fontColor=#333333;whiteSpace=wrap;gradientDirection=east;'
             'shape=startState;inIconPosition=-5,,1;verticalLabelPosition=bottom')
S_TRANSITION = ('shape=connector;labelBackgroundColor=none;endArrow=open;fontSize=12;'
                'fontFamily=Helvetica;align=center;verticalAlign=bottom;rounded=1;'
                'strokeColor=#000000;fontColor=#333333;html=1;edgeStyle=orthogonalEdgeStyle;'
                'jumpStyle=arc;jumpSize=14;fillColor=#FFE6CC;whiteSpace=nowrap;'
                'gradientColor=#FFFFFF;gradientDirection=east;startArrow=none;'
                'endSize=6;endFill=0;dashed=0;')
# Core mxGraph / draw.io UML names (see module docstring).
S_FINAL = S_INITIAL.replace('shape=startState;inIconPosition=-5,,1;', 'shape=endState;')
S_DECISION = ('rhombus;html=1;whiteSpace=wrap;fillColor=#FFF2CC;strokeColor=#808080;'
              'fontSize=12;fontFamily=Helvetica;fontColor=#333333;verticalAlign=middle;'
              'rounded=0;shadow=1')
# Partitions are drawn WITHOUT shape=swimlane.  The exported sample contains no
# partition example at all (its activity diagram is empty and no element carries
# relate_partition / partition_type), so there is no evidence for how the platform
# orients a swimlane - and an earlier attempt that relied on mxGraph's
# horizontal=0 was ignored on import.  Instead each lane is two plain rectangles,
# which cannot be re-oriented by the platform:
#   lane body   - the full-height column background
#   lane title  - a narrow full-height chip on the left, label written one
#                 character per line so it reads vertically without any rotation
#                 style key.
PARTITION_TITLE = 36
S_LANE = ('rounded=0;html=1;fillColor=#F4F8FB;strokeColor=#9AB3C7;strokeWidth=1;'
          'shadow=0;whiteSpace=wrap')
S_LANE_TITLE = ('rounded=0;html=1;fillColor=#E4EEF6;strokeColor=#9AB3C7;strokeWidth=1;'
                'shadow=0;whiteSpace=wrap;fontSize=16;fontStyle=1;fontColor=#1F4E79;'
                'verticalAlign=middle;align=center')
ACTOR = 'actor'
BOUNDARY = 'boundary'
USECASE = 'usecase'


def uid(tag: str) -> str:
    return uuid5(NAMESPACE_URL, 'AASP/A2-codearts/' + tag).hex


def jbytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def esc(text: str) -> str:
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                .replace('"', '&quot;'))


def div(text: str, maxw: int, kind: str | None = None) -> str:
    """Build the CELL_TYPE / CELL_NAME label HTML CodeArts writes into objects."""
    out = ''
    if kind:
        out += f'<div id="CELL_TYPE">&lt;&lt;{kind}&gt;&gt;</div>'
    out += ('<div id="CELL_NAME" style=" max-width: %dpx; word-wrap: break-word;'
            'margin: 0 auto;;">%s</div>' % (maxw, esc(text)))
    return out


def div_vertical(text: str, maxw: int) -> str:
    """Label HTML with one character per line: reads top-to-bottom, no rotation."""
    body = '<br>'.join(esc(ch) for ch in text if not ch.isspace())
    return ('<div id="CELL_NAME" style=" max-width: %dpx; word-wrap: break-word;'
            'margin: 0 auto;;">%s</div>' % (maxw, body))


def load_sample() -> dict:
    with zipfile.ZipFile(SOURCE) as outer:
        define = json.loads(outer.read(OLD_PREFIX + 'define.json'))
        meta_bytes = outer.read(OLD_PREFIX + '1_meta.zip')
        data_bytes = outer.read(OLD_PREFIX + '2_data.zip')
    with zipfile.ZipFile(io.BytesIO(data_bytes)) as data:
        sample = {
            'define': define,
            'meta': meta_bytes,
            'packages': json.loads(data.read('2_data/1_package/0/package.json')),
            'diagrams': json.loads(data.read('2_data/4_diagram/0/diagrams.json')),
            'elements': json.loads(data.read('2_data/2_element/0/element.json')),
            'lines': json.loads(data.read('2_data/5_line/0/t_line.json')),
        }
        sample['xml'] = {}
        for d in sample['diagrams']:
            name = f"2_data/4_diagram/0/{d['uuid']}.xml"
            try:
                sample['xml'][d['uuid']] = ET.fromstring(data.read(name))
            except KeyError:
                sample['xml'][d['uuid']] = None
    sample['_raw'] = data_bytes
    return sample


def sample_objects(sample: dict, diagram_uuid: str) -> dict[str, ET.Element]:
    xml = sample['xml'][diagram_uuid]
    return {o.get('id'): o for o in xml.findall('./root/object')}


def clone(template: ET.Element, new_id: str, name: str | None,
          geometry: tuple | None) -> ET.Element:
    node = copy.deepcopy(template)
    node.set('id', new_id)
    node.set('originCellId', new_id)
    if name is not None:
        old = node.get('pureName') or node.get('cellDefineName') or ''
        for key in ('pureName', 'cellDefineName'):
            if key in node.attrib:
                node.set(key, name)
        if 'label' in node.attrib and old:
            node.set('label', node.get('label').replace(old, name))
    if geometry is not None:
        geo = node.find('.//mxGeometry')
        for key, value in zip(('x', 'y', 'width', 'height'), geometry):
            geo.set(key, str(value))
    return node


def build_node(spec: dict, templates: dict, index: dict) -> tuple[ET.Element, dict]:
    """Return (canvas object, element.json record) for one vertex."""
    kind = spec['kind']
    eid = uid(spec['id'])
    width, height = spec.get('w', 170), spec.get('h', 64)
    if kind in ('lane', 'lane_title'):
        obj = clone(templates['state'], eid, None, (spec['x'], spec['y'], width, height))
        obj.set('type', 'Partition')
        obj.set('stereotype', 'Partition')
        obj.set('cellDefineName', 'Partition')
        obj.set('pureName', spec['name'])
        if kind == 'lane':
            obj.set('label', div('', width - 8))
            obj.find('mxCell').set('style', S_LANE)
        else:
            obj.set('label', div_vertical(spec['name'], width - 4))
            obj.find('mxCell').set('style', S_LANE_TITLE)
    elif kind == 'initial':
        obj = clone(templates['initial'], eid, None, (spec['x'], spec['y'], 30, 30))
        obj.find('mxCell').set('style', S_INITIAL)
    elif kind == 'final':
        obj = clone(templates['initial'], eid, None, (spec['x'], spec['y'], 30, 30))
        obj.set('type', 'Final')
        obj.set('stereotype', 'Final')
        obj.set('subtype', 'Final')
        obj.set('cellDefineName', 'Final')
        obj.set('pureName', 'Final')
        obj.find('mxCell').set('style', S_FINAL)
    elif kind == 'decision':
        obj = clone(templates['state'], eid, spec['name'], (spec['x'], spec['y'], width, height))
        obj.set('type', 'Decision')
        obj.set('stereotype', 'Decision')
        obj.set('cellDefineName', spec['name'])
        obj.set('pureName', spec['name'])
        obj.set('label', div(spec['name'], width - 60))
        obj.find('mxCell').set('style', S_DECISION)
    else:
        obj = clone(templates['state'], eid, spec['name'], (spec['x'], spec['y'], width, height))
        obj.set('type', spec.get('type', 'State'))
        obj.set('stereotype', spec.get('stereo', spec.get('type', 'State')))
        obj.set('cellDefineName', spec['name'])
        obj.set('pureName', spec['name'])
        obj.set('label', div(spec['name'], width - 30, spec.get('stereo', spec.get('type', 'State'))))
        obj.find('mxCell').set('style', spec.get('style', S_STATE))

    record = copy.deepcopy(index['state'])
    label = obj.get('label')
    record.update(
        name=spec['name'], uuid=eid, element_id=eid, origin_cell_id=eid,
        type=obj.get('type'), stereotype=obj.get('stereotype'),
        style=obj.find('mxCell').get('style'), value=label,
        x=str(spec['x']), y=str(spec['y']), width=str(width), height=str(height),
        element_data=ET.tostring(obj, encoding='unicode'),
        relate_partition=uid(spec['lane']) if spec.get('lane') else '',
    )
    ex = copy.deepcopy(record.get('ex') or {})
    ex.update(sub_type=obj.get('stereotype'),
              partition_type='vertical' if kind in ('lane', 'lane_title') else '')
    record['ex'] = ex
    return obj, record


def build_edge(spec: dict, templates: dict, index: dict) -> tuple[ET.Element, dict]:
    eid = uid(spec['id'])
    source, target = uid(spec['from']), uid(spec['to'])
    obj = clone(templates['transition'], eid, None, None)
    cell = obj.find('mxCell')
    cell.set('source', source)
    cell.set('target', target)
    cell.set('style', S_TRANSITION)
    label = div(spec.get('label', ''), 200) if spec.get('label') else div('', 200)
    obj.set('label', label)
    cell.set('value', label)
    points = cell.find('./mxGeometry/Array')
    for old in list(points):
        points.remove(old)
    for px, py in spec.get('waypoints', []):
        ET.SubElement(points, 'mxPoint', {'x': str(px), 'y': str(py)})

    record = copy.deepcopy(index['transition'])
    record.update(
        uuid=eid, origin_cell_id=eid, source=source, target=target,
        style=cell.get('style'), value=label, name=spec.get('label', ''),
        line_data=ET.tostring(obj, encoding='unicode'),
    )
    ex = copy.deepcopy(record.get('ex') or {})
    ex.update(subtype='Transition')
    record['ex'] = ex
    return obj, record


def build_diagram(sample: dict, spec: dict, templates: dict, index: dict,
                  now: str) -> tuple[dict, list[dict], list[dict], bytes, dict]:
    pkg_id, dia_id = uid(spec['name'] + '-pkg'), uid(spec['name'] + '-dia')
    package = copy.deepcopy(sample['packages'][0])
    package.update(name=spec['package'], uuid=pkg_id, update_time=now, create_time=now)
    package_record = copy.deepcopy(index['package'])
    package_record.update(name=spec['package'], uuid=pkg_id, element_id=pkg_id,
                          origin_cell_id=pkg_id, create_time=now, update_time=now)

    graph = ET.Element('mxGraphModel', {
        'dx': '213', 'dy': '143', 'grid': '1', 'gridSize': '10', 'guides': '1',
        'tooltips': '1', 'connect': '1', 'arrows': '1', 'fold': '1', 'page': '1',
        'pageScale': '1', 'pageWidth': str(spec['page'][0]), 'pageHeight': str(spec['page'][1]),
        'background': '#ffffff', 'math': '0', 'shadow': '0', 'version': 'v2'})
    root = ET.SubElement(graph, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0', 'style': ''})
    ET.SubElement(root, 'mxCell', {'id': '1', 'style': '', 'parent': '0'})

    elements = [package_record]
    for node in spec['nodes']:
        obj, record = build_node(node, templates, index)
        record.update(diagram_uuid=dia_id, packageuuid=pkg_id, parentuuid=pkg_id,
                      path=json.dumps({'type': 'Package', 'uuid': pkg_id}),
                      create_time=now, update_time=now)
        root.append(obj)
        elements.append(record)

    lines = []
    for edge in spec['edges']:
        obj, record = build_edge(edge, templates, index)
        record.update(diagram_uuid=dia_id, create_time=now, update_time=now)
        root.append(obj)
        lines.append(record)

    diagram = {
        'create_user': '', 'create_time': now, 'description': '', 'is_delete': '',
        'name': spec['name'], 'update_time': now, 'update_user': '',
        'uuid': dia_id, 'packageuuid': pkg_id, 'template_name': '',
        'main_typeuuid': UML_PARENT, 'stereotypeuuid': spec['typeuuid'],
        'parentuuid': '', 'path': json.dumps({'type': 'Package', 'uuid': pkg_id}),
        'show_stereotype': '', 'show_from_tag': '', 'tag': '', 'auto_resize': '',
        'is_static_diagram': '', 'watermark': False, 'is_overview_diagram': '',
        'sequence': 0, 'show_from_package': '', 'setting': None,
    }
    canvas = ET.tostring(graph, encoding='utf-8', xml_declaration=True)
    return package, elements, lines, canvas, diagram


def build_zip(sample: dict, templates: dict, index: dict, out_name: str,
              specs: list[dict]) -> Path:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    packages, elements, lines, diagram_records, canvases = [], [], [], [], {}
    for spec in specs:
        package, elems, lns, canvas, diagram = build_diagram(sample, spec, templates, index, now)
        packages.append(package)
        elements.extend(elems)
        lines.extend(lns)
        diagram_records.append(diagram)
        canvases[diagram['uuid']] = canvas

    data_files = {
        '2_data/1_package/0/package.json': jbytes(packages),
        '2_data/2_element/0/element.json': jbytes(elements),
        '2_data/3_element_relation/0/element_attribute.json': jbytes({}),
        '2_data/3_element_relation/0/element_operation.json': jbytes({}),
        '2_data/4_diagram/0/diagrams.json': jbytes(diagram_records),
        '2_data/5_line/0/t_line.json': jbytes(lines),
    }
    for dia_uuid, canvas in canvases.items():
        data_files[f'2_data/4_diagram/0/{dia_uuid}.xml'] = canvas
    new_data = make_zip(data_files)
    define = copy.deepcopy(sample['define'])
    define['data_file_hex'] = hashlib.sha512(new_data).hexdigest()
    define['meta_data_file_hex'] = hashlib.sha512(sample['meta']).hexdigest()
    define['create_time'] = now
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / out_name
    out.write_bytes(make_zip({
        OLD_PREFIX + 'define.json': jbytes(define),
        OLD_PREFIX + '1_meta.zip': sample['meta'],
        OLD_PREFIX + '2_data.zip': new_data,
    }))
    return out


def build_templates(sample: dict) -> tuple[dict, dict]:
    """Clone real canvas objects of the sample to reuse as shape templates."""
    state_objs = sample_objects(sample, 'c66b89b212d145f68d4634d47e414c34')
    yl_objs = sample_objects(sample, '45c05e9b4f6d45a2bc6975ebb880c328')
    elements = sample['elements']
    lines = sample['lines']

    def by_uuid(seq, u):
        return next(x for x in seq if x['uuid'] == u)

    state_el = next(e for e in elements if e.get('name') == 'State1')
    transition_ln = next(l for l in lines if l.get('type') == 'transition')
    initial_obj = next(o for o in state_objs.values() if o.get('type') == 'Initial')
    state_obj = next(o for o in state_objs.values() if o.get('type') == 'State')
    transition_obj = next(o for o in state_objs.values() if o.get('type') == 'transition')
    package_el = next(e for e in elements
                      if e['uuid'] in {p['uuid'] for p in sample['packages']})

    templates = {
        'state': state_obj,
        'initial': initial_obj,
        'transition': transition_obj,
        'actor': next(o for o in yl_objs.values() if o.get('type') == 'Actor'),
        'boundary': next(o for o in yl_objs.values() if o.get('type') == 'Boundary'),
        'usecase': next(o for o in yl_objs.values() if o.get('type') == 'UseCase'),
        'connector': next(o for o in yl_objs.values() if o.get('type') == 'default edge'),
    }
    index = {'state': state_el, 'transition': transition_ln, 'package': package_el}
    return templates, index


# --------------------------------------------------------------------------
# Diagram content.  Coordinates are canvas pixels; lanes are swimlane objects.
# --------------------------------------------------------------------------

LANE_APPLICANT, LANE_PLATFORM, LANE_ADMIN = 'lane-app', 'lane-plat', 'lane-adm'

ACTIVITY_CLAIM = {
    'name': 'A2-认领审核活动图',
    'package': '认领审核流程',
    'typeuuid': T_UML_ACTIVITY,
    # x/y are the TOP-LEFT corner of each cell, matching mxGeometry.  Each lane
    # reserves PARTITION_TITLE px of its left edge for the rotated title strip,
    # so lane content starts at lane.x + PARTITION_TITLE.
    'page': (1610, 1600),
    'lanes': [
        (LANE_APPLICANT, '申请人', 30, 100, 340, 1440),
        (LANE_PLATFORM, '平台系统', 380, 100, 680, 1440),
        (LANE_ADMIN, '授权管理员', 1080, 100, 490, 1440),
    ],
    'nodes': [
        ('act-start', 'initial', '初始', 203, 170, 30, 30, LANE_APPLICANT),
        ('act-locate', 'action', '申请人定位目标学者门户', 78, 250, 280, 60, LANE_APPLICANT),
        ('act-submit', 'action', '填写身份信息与佐证并提交', 78, 350, 280, 60, LANE_APPLICANT),
        # main column of 平台系统, kept clear so the happy path is a straight run
        ('act-valid', 'decision', '必填、格式、重复申请校验通过？', 490, 200, 300, 150, LANE_PLATFORM),
        ('act-recorded', 'action', '保存申请编号与提交快照\n状态 submitted', 480, 490, 320, 64, LANE_PLATFORM),
        ('act-verify', 'action', '核验证据与目标门户归属\n状态 verifying', 480, 590, 320, 64, LANE_PLATFORM),
        ('act-sufficient', 'decision', '证据足够且门户归属可判定？', 490, 690, 300, 150, LANE_PLATFORM),
        ('act-conflict', 'decision', '已有管理人或并发争议？', 490, 880, 300, 150, LANE_PLATFORM),
        # error branch of 平台系统, offset right of the main column
        ('act-fix', 'action', '返回具体错误或既有申请编号', 770, 390, 260, 64, LANE_PLATFORM),
        ('act-notify1', 'action', '通知申请人可见结果，允许按 B1 补证重提', 450, 1150, 380, 64, LANE_PLATFORM),
        ('act-end1', 'final', '结束', 625, 1250, 30, 30, LANE_PLATFORM),
        ('act-notify2', 'action', '通知申请人并允许管理目标门户', 450, 1360, 380, 64, LANE_PLATFORM),
        ('act-end2', 'final', '结束', 625, 1460, 30, 30, LANE_PLATFORM),
        ('act-reject', 'action', '管理员记录驳回理由\n状态 rejected', 1143, 690, 400, 64, LANE_ADMIN),
        ('act-hold', 'action', '暂停直接通过并转争议核验\n不得覆盖现有管理人', 1143, 880, 400, 76, LANE_ADMIN),
        ('act-review', 'action', '有权限管理员审核申请与版本', 1143, 1010, 400, 64, LANE_ADMIN),
        ('act-approved', 'decision', '批准？', 1183, 1130, 320, 140, LANE_ADMIN),
        ('act-grant', 'action', '原子记录 approved 与目标门户管理权限\n保存审核人、时间、依据和日志',
         1143, 1290, 400, 76, LANE_ADMIN),
    ],
    'edges': [
        ('e01', 'act-start', 'act-locate', '', []),
        ('e02', 'act-locate', 'act-submit', '', []),
        ('e03', 'act-submit', 'act-valid', '', []),
        ('e04', 'act-valid', 'act-fix', '否', []),
        ('e05', 'act-fix', 'act-submit', '修正后重新提交', [(430, 422)]),
        ('e06', 'act-valid', 'act-recorded', '是', []),
        ('e07', 'act-recorded', 'act-verify', '', []),
        ('e08', 'act-verify', 'act-sufficient', '', []),
        ('e09', 'act-sufficient', 'act-reject', '否', []),
        ('e10', 'act-sufficient', 'act-conflict', '是', []),
        ('e11', 'act-conflict', 'act-hold', '是', [(1070, 955)]),
        ('e12', 'act-hold', 'act-reject', '', [(1556, 918), (1556, 722)]),
        ('e13', 'act-conflict', 'act-review', '否', [(1070, 1042)]),
        ('e14', 'act-review', 'act-approved', '', []),
        ('e15', 'act-approved', 'act-reject', '否', [(1129, 1200), (1129, 722)]),
        ('e16', 'act-approved', 'act-grant', '是', []),
        ('e17', 'act-reject', 'act-notify1', '', [(1010, 722), (1010, 1182)]),
        ('e18', 'act-grant', 'act-notify2', '', [(1030, 1328), (1030, 1392)]),
        ('e19', 'act-notify1', 'act-end1', '', []),
        ('e20', 'act-notify2', 'act-end2', '', []),
    ],
}

STATE_COLLECT = {
    'name': 'A2-采集任务状态图',
    'package': '采集任务状态机',
    'typeuuid': T_UML_STATEMACHINE,
    'page': (1280, 740),
    'lanes': [],
    'nodes': [
        ('st-init', 'initial', '初始', 485, 90, 30, 30, None),
        ('st-queued', 'state', 'queued（待执行）', 500, 180, 240, 64, None),
        ('st-running', 'state', 'running（运行中）', 500, 300, 240, 64, None),
        ('st-succeeded', 'state', 'succeeded（成功）', 960, 300, 240, 64, None),
        ('st-failed', 'state', 'failed（失败）', 500, 470, 240, 64, None),
        ('st-retrying', 'state', 'retrying（重试中）', 140, 470, 240, 64, None),
        ('st-stopped', 'state', 'stopped（已停止）', 960, 470, 240, 64, None),
        ('st-final-succ', 'final', '结束', 1160, 317, 30, 30, None),
        ('st-final-fail', 'final', '结束', 500, 650, 30, 30, None),
        ('st-final-stop', 'final', '结束', 1160, 487, 30, 30, None),
    ],
    'edges': [
        ('s01', 'st-init', 'st-queued', '创建合法任务', []),
        ('s02', 'st-queued', 'st-running', '管理员启动/调度启动', []),
        ('s03', 'st-running', 'st-succeeded', '全批次完成且满足成功口径', []),
        ('s04', 'st-running', 'st-failed', '源站/解析/写入失败', []),
        ('s05', 'st-running', 'st-stopped', '管理员停止', [(700, 332), (700, 502)]),
        ('s06', 'st-failed', 'st-retrying', '重试未满 3 次', []),
        ('s07', 'st-retrying', 'st-running', '退避结束，幂等续跑', [(140, 410)]),
        ('s08', 'st-retrying', 'st-stopped', '管理员停止', [(140, 620), (960, 620)]),
        ('s09', 'st-failed', 'st-final-fail', '放弃或达到上限', []),
        ('s10', 'st-succeeded', 'st-final-succ', '', []),
        ('s11', 'st-stopped', 'st-final-stop', '', []),
    ],
}

STATE_CLAIM = {
    'name': 'A2-认领申请状态图',
    'package': '认领申请状态机',
    'typeuuid': T_UML_STATEMACHINE,
    'page': (1169, 740),
    'lanes': [],
    'nodes': [
        ('sc-init', 'initial', '初始', 365, 90, 30, 30, None),
        ('sc-submitted', 'state', 'submitted（已提交）', 380, 200, 230, 64, None),
        ('sc-verifying', 'state', 'verifying（核验中）', 380, 330, 230, 64, None),
        ('sc-approved', 'state', 'approved（已通过）', 380, 460, 230, 64, None),
        ('sc-rejected', 'state', 'rejected（已驳回）', 380, 590, 230, 64, None),
        ('sc-cancelled', 'state', 'cancelled（已取消）', 800, 330, 230, 64, None),
        ('sc-disputed', 'state', 'disputed（争议）', 800, 460, 230, 64, None),
        ('sc-final', 'final', '结束', 1000, 347, 30, 30, None),
    ],
    'edges': [
        ('c01', 'sc-init', 'sc-submitted', 'UC02 保存申请编号与材料引用', []),
        ('c02', 'sc-submitted', 'sc-verifying', '进入核验队列', []),
        ('c03', 'sc-submitted', 'sc-cancelled', '申请人取消', [(560, 232), (560, 298)]),
        ('c04', 'sc-verifying', 'sc-cancelled', '申请人取消且尚未终局处理', []),
        ('c05', 'sc-verifying', 'sc-approved', 'UC03 审核通过并授目标门户权限', []),
        ('c06', 'sc-verifying', 'sc-rejected', 'UC03 驳回并记录理由', [(180, 362), (180, 622)]),
        ('c07', 'sc-approved', 'sc-disputed', '批准后出现身份争议', []),
        ('c08', 'sc-rejected', 'sc-submitted', '申请人补证重提（新处理轮次）', [(140, 622), (140, 200)]),
        ('c09', 'sc-cancelled', 'sc-final', '', []),
    ],
}

SPEC_ETL = {
    'name': 'A2-SPEC-ETL-01 清洗与标准化流程',
    'package': 'SPEC-ETL-01',
    'typeuuid': T_UML_ACTIVITY,
    'page': (1169, 1180),
    'lanes': [],
    'nodes': [
        ('etl-start', 'initial', '开始', 195, 90, 30, 30, None),
        ('etl-in', 'action', '接收原始行与来源信息\n（来源标识 / 许可 / 获取时间 / 批次行号）', 200, 175, 340, 76, None),
        ('etl-struct', 'action', '结构校验：编码、CSV 引号、\nBibTeX 语法、单批 1000 条 / 10MB', 200, 300, 340, 76, None),
        ('etl-struct-ok', 'decision', '结构校验通过？', 200, 440, 280, 140, None),
        ('etl-isolate', 'action', '隔离该行，记录行号与字段错误，\n不写入正式成果', 620, 440, 340, 76, None),
        ('etl-type', 'action', '类型映射：仅接受固定七类，\n未知类型标待映射，不擅自改成论文', 200, 580, 340, 76, None),
        ('etl-text', 'action', '文本规范：去空白、统一编码、长度上限，\n保留原文本，不自动译名或编造 DOI', 200, 700, 340, 76, None),
        ('etl-date', 'action', '日期分列：成果年度 / 正式日期 /\n首发日期 / 来源列表日期', 200, 820, 340, 76, None),
        ('etl-id', 'action', '标识与来源规范：DOI 规范化，\n专利号 / 软著号 / 立项号分列', 200, 940, 340, 76, None),
        ('etl-status', 'action', '字段状态标注：有 / 缺失 / 不适用 / 无法核验，\n冲突字段保留原值', 200, 1060, 340, 76, None),
        ('etl-preview', 'action', '预览与幂等确认\n（用户 + 幂等键 + 文件摘要 + 批次版本）', 700, 700, 340, 90, None),
        ('etl-next', 'action', '送去重与消歧', 700, 900, 340, 76, None),
        ('etl-end', 'final', '结束', 870, 1040, 30, 30, None),
    ],
    'edges': [
        ('t01', 'etl-start', 'etl-in', '', []),
        ('t02', 'etl-in', 'etl-struct', '', []),
        ('t03', 'etl-struct', 'etl-struct-ok', '', []),
        ('t04', 'etl-struct-ok', 'etl-isolate', '否', []),
        ('t05', 'etl-struct-ok', 'etl-type', '是', []),
        ('t06', 'etl-type', 'etl-text', '', []),
        ('t07', 'etl-text', 'etl-date', '', []),
        ('t08', 'etl-date', 'etl-id', '', []),
        ('t09', 'etl-id', 'etl-status', '', []),
        ('t10', 'etl-status', 'etl-preview', '', [(560, 1098), (560, 745)]),
        ('t11', 'etl-preview', 'etl-next', '', []),
        ('t12', 'etl-next', 'etl-end', '', []),
        ('t13', 'etl-isolate', 'etl-preview', '逐行处置随批次汇总', [(1075, 478), (1075, 660)]),
    ],
}

SPEC_DEDUP = {
    'name': 'A2-SPEC-DEDUP-01 成果去重流程',
    'package': 'SPEC-DEDUP-01',
    'typeuuid': T_UML_ACTIVITY,
    'page': (1169, 900),
    'lanes': [],
    'nodes': [
        ('dd-start', 'initial', '开始', 170, 90, 30, 30, None),
        ('dd-in', 'action', '已标准化记录', 175, 180, 280, 64, None),
        ('dd-key', 'action', '同源记录键与内容摘要比对', 175, 300, 280, 64, None),
        ('dd-same', 'decision', '同源同内容？', 175, 440, 260, 140, None),
        ('dd-skip', 'action', '标记 SKIPPED_IDEMPOTENT\n不重复入库', 560, 440, 280, 76, None),
        ('dd-doi', 'action', '查有效规范化 DOI / 类型标识，\n检索相似题名-作者-年度候选', 175, 610, 300, 90, None),
        ('dd-dup', 'decision', '同有效 DOI 已有公开记录？', 175, 760, 300, 140, None),
        ('dd-block', 'action', '标记 REVIEW_REQUIRED：\n阻止直接公开，记录例外理由与审核版本', 620, 760, 320, 90, None),
        ('dd-cand', 'decision', '存在相似候选？', 175, 940, 280, 140, None),
        ('dd-review', 'action', '标记 REVIEW_REQUIRED\n给出证据与差异供人工确认', 620, 940, 320, 76, None),
        ('dd-new', 'action', '新建草稿并分配新 achievement_id', 175, 1090, 300, 64, None),
        ('dd-end', 'final', '结束', 325, 1180, 30, 30, None),
    ],
    'edges': [
        ('d01', 'dd-start', 'dd-in', '', []),
        ('d02', 'dd-in', 'dd-key', '', []),
        ('d03', 'dd-key', 'dd-same', '', []),
        ('d04', 'dd-same', 'dd-skip', '是', []),
        ('d05', 'dd-same', 'dd-doi', '否', []),
        ('d06', 'dd-doi', 'dd-dup', '', []),
        ('d07', 'dd-dup', 'dd-block', '是', []),
        ('d08', 'dd-dup', 'dd-cand', '否', []),
        ('d09', 'dd-cand', 'dd-review', '是', []),
        ('d10', 'dd-cand', 'dd-new', '否', []),
        ('d11', 'dd-new', 'dd-end', '', []),
    ],
}

SPEC_DISAMB = {
    'name': 'A2-SPEC-DISAMB-01 学者消歧流程',
    'package': 'SPEC-DISAMB-01',
    'typeuuid': T_UML_ACTIVITY,
    'page': (1169, 900),
    'lanes': [],
    'nodes': [
        ('da-start', 'initial', '开始', 180, 90, 30, 30, None),
        ('da-in', 'action', '作者原始姓名与单位信息', 185, 180, 300, 64, None),
        ('da-store', 'action', '存有序 AchievementAuthor 与来源姓名，\nPerson 与登录 User 分离，\n已有 Person 匹配仅为候选', 185, 300, 340, 76, None),
        ('da-match', 'action', '匹配已有 Person（仅作为候选）', 185, 420, 340, 64, None),
        ('da-show', 'action', '展示候选：署名来源、机构、\n已核验标识与相互冲突字段', 185, 540, 340, 76, None),
        ('da-human', 'decision', '人工决定', 185, 680, 260, 140, None),
        ('da-same', 'action', '确认同人：关联既有 Person', 560, 630, 300, 64, None),
        ('da-diff', 'action', '确认不同人：新建 Person', 560, 740, 300, 64, None),
        ('da-hold', 'action', '暂缓：保留待核验', 560, 850, 300, 64, None),
        ('da-audit', 'action', '保存操作者、证据、时间与版本\n同名同机构不自动合并', 900, 740, 240, 90, None),
        ('da-end', 'final', '结束', 1020, 880, 30, 30, None),
    ],
    'edges': [
        ('a01', 'da-start', 'da-in', '', []),
        ('a02', 'da-in', 'da-store', '', []),
        ('a03', 'da-store', 'da-match', '', []),
        ('a04', 'da-match', 'da-show', '', []),
        ('a05', 'da-show', 'da-human', '', []),
        ('a06', 'da-human', 'da-same', '同人', []),
        ('a07', 'da-human', 'da-diff', '不同人', []),
        ('a08', 'da-human', 'da-hold', '暂缓', []),
        ('a09', 'da-same', 'da-audit', '', []),
        ('a10', 'da-diff', 'da-audit', '', []),
        ('a11', 'da-hold', 'da-audit', '', []),
        ('a12', 'da-audit', 'da-end', '', []),
    ],
}

SPEC_SEARCH = {
    'name': 'A2-SPEC-SEARCH-01 检索排序与分面流程',
    'package': 'SPEC-SEARCH-01',
    'typeuuid': T_UML_ACTIVITY,
    'page': (1169, 1180),
    'lanes': [],
    'nodes': [
        ('se-start', 'initial', '开始', 210, 90, 30, 30, None),
        ('se-parse', 'action', '解析请求参数：关键词 / 类型 / 领域 / 机构 /\n作者 / 年份口径 / 排序 / 页码与页大小', 215, 175, 400, 76, None),
        ('se-auth', 'action', '按当前身份建立可读集合（先鉴权，再检索）', 215, 300, 400, 64, None),
        ('se-match', 'action', '在可读集合上执行全文与元数据匹配', 215, 400, 400, 64, None),
        ('se-count', 'action', '计算结果总数与分面计数（只计可读记录）', 215, 500, 400, 64, None),
        ('se-sort', 'action', '排序：有效 DOI 置前 → 相关度 →\n成果年度降序 → 稳定 achievement_id', 215, 600, 400, 76, None),
        ('se-page', 'action', '稳定分页（默认 20，最大 100）', 215, 720, 400, 64, None),
        ('se-guard', 'action', '详情/附件/引用/导出/门户入口再次服务端鉴权', 215, 820, 400, 76, None),
        ('se-visible', 'decision', '对象可读且已发布？', 215, 960, 300, 140, None),
        ('se-404', 'action', '统一按 404 返回，不泄露对象存在性', 640, 960, 320, 76, None),
        ('se-out', 'action', '返回结果、分面、当前条件与状态说明\n（失败 / 零结果 / 权限不足 / 未采集分列）', 700, 700, 340, 90, None),
        ('se-end', 'final', '结束', 870, 960 + 150, 30, 30, None),
    ],
    'edges': [
        ('q01', 'se-start', 'se-parse', '', []),
        ('q02', 'se-parse', 'se-auth', '', []),
        ('q03', 'se-auth', 'se-match', '', []),
        ('q04', 'se-match', 'se-count', '', []),
        ('q05', 'se-count', 'se-sort', '', []),
        ('q06', 'se-sort', 'se-page', '', []),
        ('q07', 'se-page', 'se-guard', '', []),
        ('q08', 'se-guard', 'se-visible', '', []),
        ('q09', 'se-visible', 'se-404', '否', []),
        ('q10', 'se-visible', 'se-out', '是', [(430, 760)]),
        ('q11', 'se-out', 'se-end', '', []),
    ],
}

# --------------------------------------------------------------------------

OUTPUTS = [
    ('A2-认领审核活动图.zip', [ACTIVITY_CLAIM]),
    ('A2-采集任务状态图.zip', [STATE_COLLECT]),
    ('A2-认领申请状态图.zip', [STATE_CLAIM]),
    ('A2-SPEC核心模块流程图集.zip', [SPEC_ETL, SPEC_DEDUP, SPEC_DISAMB, SPEC_SEARCH]),
]


def main() -> None:
    sample = load_sample()
    templates, index = build_templates(sample)
    # Each diagram spec lists its nodes as tuples; normalise into dicts.
    for _, specs in OUTPUTS:
        for spec in specs:
            spec['nodes'] = [
                {'id': n[0], 'kind': n[1], 'name': n[2], 'x': n[3], 'y': n[4],
                 'w': n[5], 'h': n[6], 'lane': n[7]}
                for n in spec['nodes']
            ]
            spec['edges'] = [
                {'id': e[0], 'from': e[1], 'to': e[2], 'label': e[3], 'waypoints': e[4]}
                for e in spec['edges']
            ]
            expanded = []
            for lid, lname, lx, ly, lw, lh in spec['lanes']:
                expanded.append({'id': lid, 'kind': 'lane', 'name': lname, 'x': lx,
                                 'y': ly, 'w': lw, 'h': lh, 'lane': None})
                expanded.append({'id': lid + '-title', 'kind': 'lane_title', 'name': lname,
                                 'x': lx, 'y': ly, 'w': PARTITION_TITLE, 'h': lh, 'lane': None})
            spec['nodes'] = expanded + spec['nodes']
            spec['lanes'] = []
    for out_name, specs in OUTPUTS:
        path = build_zip(sample, templates, index, out_name, specs)
        print(f'{path.name}  ({path.stat().st_size} bytes, {len(specs)} diagram(s))')


if __name__ == '__main__':
    main()
