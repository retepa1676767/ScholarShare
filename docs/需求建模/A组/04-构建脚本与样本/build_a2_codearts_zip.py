"""Create an A2 CodeArts model-project ZIP from the user's own export.

The ZIP format is not a public schema. Keep the template's metadata and
record shapes, then validate every local cross-file reference before export.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from xml.etree import ElementTree as ET


HERE = Path(__file__).resolve().parent
A_GROUP = HERE.parent
OUT_DIR = A_GROUP / '02-模型图' / '用例图'
# Prefer the sample that travels with the repository.
_LOCAL = HERE / 'test1_master_20261012184125.zip'
SOURCE = _LOCAL if _LOCAL.exists() else Path('/Users/hjl/Downloads/test1_master_20261012184125.zip')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'sample'
if MODE not in ('sample', 'uml'):
    raise SystemExit('usage: build_a2_codearts_zip.py [sample|uml]')
OUTPUT = OUT_DIR / ('A2-学术成果分享平台-UML用例图-试验.zip' if MODE == 'uml'
                    else 'A2-学术成果分享平台-CodeArts模型工程.zip')
OLD_PREFIX = 'test1_master_20261012184125/'
PACKAGE_NAME = '学术成果分享平台'
DIAGRAM_NAME = 'A2-系统用例图'
SYSTEM_NAME = '学术成果分享平台'


def uid(name: str) -> str:
    return uuid5(NAMESPACE_URL, 'AASP/A2/' + name).hex


PACKAGE_ID = uid('package')
DIAGRAM_ID = uid('diagram')
ACTORS = [
    ('ACT01', '访客', 130, 195),
    ('ACT02', '科研人员（申请人）', 130, 365),
    ('ACT03', '已认领学者', 130, 535),
    ('ACT04', '平台管理员', 1255, 365),
]
USE_CASES = [
    ('UC04', '检索并查看成果', 445, 195),
    ('UC06', '查看成果统计', 855, 195),
    ('UC02', '申请认领学者门户', 445, 365),
    ('UC05', '管理本人已认领成果', 855, 365),
    ('UC01', '管理数据采集任务', 445, 555),
    ('UC03', '审核门户认领申请', 855, 555),
]
ASSOCIATIONS = [
    ('ACT01', 'UC04'), ('ACT01', 'UC06'),
    ('ACT02', 'UC02'), ('ACT03', 'UC05'),
    ('ACT04', 'UC01'), ('ACT04', 'UC03'), ('ACT04', 'UC06'),
]
EDGE_WAYPOINTS = {
    ('ACT01', 'UC06'): [(300, 90), (970, 90)],
    ('ACT03', 'UC05'): [(310, 495), (740, 495)],
    ('ACT04', 'UC01'): [(1210, 710), (680, 710)],
    ('ACT04', 'UC03'): [(1200, 600)],
}


def jbytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def clone_object(node: ET.Element, new_id: str, name: str | None = None,
                 geometry: tuple[int, int, int, int] | None = None) -> ET.Element:
    node = copy.deepcopy(node)
    node.set('id', new_id)
    if name is not None:
        old_name = node.get('pureName') or node.get('cellDefineName') or ''
        for key in ('pureName', 'cellDefineName'):
            if key in node.attrib:
                node.set(key, name)
        if 'label' in node.attrib:
            node.set('label', node.get('label', '').replace(old_name, name))
    if geometry is not None:
        geo = node.find('.//mxGeometry')
        assert geo is not None
        for key, value in zip(('x', 'y', 'width', 'height'), geometry):
            geo.set(key, str(value))
    return node


def main() -> None:
    with zipfile.ZipFile(SOURCE) as outer:
        define = json.loads(outer.read(OLD_PREFIX + 'define.json'))
        meta_bytes = outer.read(OLD_PREFIX + '1_meta.zip')
        data_bytes = outer.read(OLD_PREFIX + '2_data.zip')
    with zipfile.ZipFile(io.BytesIO(data_bytes)) as data:
        packages = json.loads(data.read('2_data/1_package/0/package.json'))
        diagrams = json.loads(data.read('2_data/4_diagram/0/diagrams.json'))
        elements = json.loads(data.read('2_data/2_element/0/element.json'))
        lines = json.loads(data.read('2_data/5_line/0/t_line.json'))
        yl = next(d for d in diagrams if d['name'] == 'yl')
        old_package_id = yl['packageuuid']
        old_diagram_id = yl['uuid']
        old_xml = ET.fromstring(data.read(f'2_data/4_diagram/0/{old_diagram_id}.xml'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    package = copy.deepcopy(next(p for p in packages if p['uuid'] == old_package_id))
    package.update(name=PACKAGE_NAME, uuid=PACKAGE_ID, update_time=now, create_time=now)
    package_record = copy.deepcopy(next(e for e in elements if e['uuid'] == old_package_id))
    package_record.update(name=PACKAGE_NAME, uuid=PACKAGE_ID,
                          element_id=PACKAGE_ID, origin_cell_id=PACKAGE_ID,
                          create_time=now, update_time=now)
    diagram = copy.deepcopy(yl)
    diagram.update(name=DIAGRAM_NAME, uuid=DIAGRAM_ID, packageuuid=PACKAGE_ID,
                   path=json.dumps({'type': 'Package', 'uuid': PACKAGE_ID}),
                   create_time=now, update_time=now, sequence=0)
    if MODE == 'uml':
        # Present in the sample's view-type metadata but not in its diagram list.
        diagram['main_typeuuid'] = 'ff1ee18c-ac06-11e8-9e12-0242ac117104'
        diagram['stereotypeuuid'] = 'ff1ee4d6-ac06-11e8-9e12-0242ac117104'

    originals = {e.get('id'): e for e in old_xml.findall('./root/object')}
    actor_template = originals['2cbed51d01f342d2d0db38a281f2a9cb']
    actor_text_template = originals['1e14aadda9bc4c0e8502381a4d75d81e']
    mount_link_template = originals['7a872d1058bf4ea5f9f37787e0fbda70']
    boundary_template = originals['a4b045dc545b4b19fe89abbba93291b0']
    usecase_template = originals['b70df828f6c248ba8e752f62cf2dc8cf']
    edge_template = originals['b40c17cdd1494e46bc7a40a035653925']
    actor_record = next(e for e in elements if e['uuid'] == actor_template.get('id'))
    usecase_record = next(e for e in elements if e['uuid'] == usecase_template.get('id'))
    mount_record = next(e for e in lines if e['uuid'] == mount_link_template.get('id'))
    edge_record = next(e for e in lines if e['uuid'] == edge_template.get('id'))

    graph = ET.Element('mxGraphModel', old_xml.attrib)
    graph.set('pageWidth', '1500')
    graph.set('pageHeight', '900')
    root = ET.SubElement(graph, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0', 'style': ''})
    ET.SubElement(root, 'mxCell', {'id': '1', 'style': '', 'parent': '0'})
    new_elements = [package_record]
    new_lines: list[dict] = []

    boundary = clone_object(boundary_template, uid('boundary'), SYSTEM_NAME,
                            (330, 110, 850, 680))
    boundary.set('originCellId', boundary.get('id'))
    root.append(boundary)

    for code, title, x, y in ACTORS:
        name = f'{code} {title}'
        actor_id, text_id, mount_id = uid(code), uid(code + '-label'), uid(code + '-label-link')
        actor = clone_object(actor_template, actor_id, name, (x, y, 35, 50))
        root.append(actor)
        label = clone_object(actor_text_template, text_id, name, (-90, 48, 220, 42))
        label.set('originCellId', text_id)
        label.set('label', label.get('label', '').replace('130px', '220px'))
        label.find('mxCell').set('parent', actor_id)
        # The sample's label is an HTML fragment with the actor name.
        root.append(label)
        mount = clone_object(mount_link_template, mount_id)
        cell = mount.find('mxCell')
        cell.set('parent', actor_id)
        cell.set('source', actor_id)
        cell.set('target', text_id)
        root.append(mount)
        e = copy.deepcopy(actor_record)
        e.update(name=name, uuid=actor_id, element_id=actor_id,
                 origin_cell_id=actor_id, diagram_uuid=DIAGRAM_ID,
                 packageuuid=PACKAGE_ID, parentuuid=PACKAGE_ID,
                 path=json.dumps({'type': 'Package', 'uuid': PACKAGE_ID}),
                 x=str(x), y=str(y), width='35', height='50',
                 element_data=ET.tostring(actor, encoding='unicode'),
                 create_time=now, update_time=now)
        new_elements.append(e)
        line = copy.deepcopy(mount_record)
        line.update(uuid=mount_id, origin_cell_id=mount_id, diagram_uuid=DIAGRAM_ID,
                    source=actor_id, target=text_id, parent_link=actor_id,
                    line_data=ET.tostring(mount, encoding='unicode'),
                    create_time=now, update_time=now)
        new_lines.append(line)

    for code, title, x, y in USE_CASES:
        name = f'{code} {title}'
        element_id = uid(code)
        usecase = clone_object(usecase_template, element_id, name, (x, y, 230, 75))
        # Keep the HTML label width consistent with the larger ellipse.
        usecase.set('label', re.sub(r'max-width: \d+px', 'max-width: 220px', usecase.get('label', '')))
        root.append(usecase)
        e = copy.deepcopy(usecase_record)
        e.update(name=name, uuid=element_id, element_id=element_id,
                 origin_cell_id=element_id, diagram_uuid=DIAGRAM_ID,
                 packageuuid=PACKAGE_ID, parentuuid=PACKAGE_ID,
                 path=json.dumps({'type': 'Package', 'uuid': PACKAGE_ID}),
                 x=str(x), y=str(y), width='230', height='75',
                 value=usecase.get('label'),
                 element_data=ET.tostring(usecase, encoding='unicode'),
                 create_time=now, update_time=now)
        if isinstance(e.get('attr'), dict):
            e['attr']['name'] = name
            e['attr']['uuid'] = uid(code + '-attr')
            e['attr']['create_time'] = now
            e['attr']['update_time'] = now
        new_elements.append(e)

    for source_code, target_code in ASSOCIATIONS:
        line_id = uid(source_code + '-' + target_code)
        edge = clone_object(edge_template, line_id)
        cell = edge.find('mxCell')
        cell.set('source', uid(source_code))
        cell.set('target', uid(target_code))
        cell.set('style', cell.get('style', '').replace('endArrow=classic', 'endArrow=none'))
        points = cell.find('./mxGeometry/Array')
        assert points is not None
        for old_point in list(points):
            points.remove(old_point)
        for px, py in EDGE_WAYPOINTS.get((source_code, target_code), []):
            ET.SubElement(points, 'mxPoint', {'x': str(px), 'y': str(py)})
        root.append(edge)
        line = copy.deepcopy(edge_record)
        line.update(uuid=line_id, origin_cell_id=line_id, diagram_uuid=DIAGRAM_ID,
                    source=uid(source_code), target=uid(target_code),
                    style=cell.get('style'), line_data=ET.tostring(edge, encoding='unicode'),
                    create_time=now, update_time=now)
        new_lines.append(line)

    data_files = {
        '2_data/1_package/0/package.json': jbytes([package]),
        '2_data/2_element/0/element.json': jbytes(new_elements),
        '2_data/3_element_relation/0/element_attribute.json': jbytes({}),
        '2_data/3_element_relation/0/element_operation.json': jbytes({}),
        '2_data/4_diagram/0/diagrams.json': jbytes([diagram]),
        f'2_data/4_diagram/0/{DIAGRAM_ID}.xml': ET.tostring(graph, encoding='utf-8', xml_declaration=True),
        '2_data/5_line/0/t_line.json': jbytes(new_lines),
    }
    new_data = make_zip(data_files)
    define['data_file_hex'] = hashlib.sha512(new_data).hexdigest()
    define['meta_data_file_hex'] = hashlib.sha512(meta_bytes).hexdigest()
    define['create_time'] = now
    out_files = {
        OLD_PREFIX + 'define.json': jbytes(define),
        OLD_PREFIX + '1_meta.zip': meta_bytes,
        OLD_PREFIX + '2_data.zip': new_data,
    }
    OUTPUT.write_bytes(make_zip(out_files))
    print(OUTPUT)


if __name__ == '__main__':
    main()
