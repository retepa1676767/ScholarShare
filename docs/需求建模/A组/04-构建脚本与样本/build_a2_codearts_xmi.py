"""Build a conservative CodeArts XMI from the user's exported sample shape."""

from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from xml.sax.saxutils import escape


HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / '02-模型图' / '用例图'
OUTPUT = OUT_DIR / "A2-系统用例图.xmi"
PACKAGE = "学术成果分享平台-A2系统用例图"
ACTORS = [
    ("ACT01", "访客"),
    ("ACT02", "科研人员（申请人）"),
    ("ACT03", "已认领学者"),
    ("ACT04", "平台管理员"),
]
USE_CASES = [
    ("UC01", "管理数据采集任务"),
    ("UC02", "申请认领学者门户"),
    ("UC03", "审核门户认领申请"),
    ("UC04", "检索并查看成果"),
    ("UC05", "管理本人已认领成果"),
    ("UC06", "查看成果统计"),
]


def element(kind: str, code: str, title: str) -> str:
    name = escape(f"{code} {title}", {'"': '&quot;'})
    element_id = uuid5(NAMESPACE_URL, f"AASP/A2/{code}").hex
    return (
        '      <packagedElement xmlns:xmi="http://www.omg.org/spec/XMI/20131001" '
        f'name="{name}" xmi:id="{element_id}" xmi:type="uml:{kind}"/>'
    )


package_id = uuid5(NAMESPACE_URL, "AASP/A2/package").hex
lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<xmi:XMI xmlns:xmi="http://www.omg.org/spec/XMI/20131001" xmlns:uml="http://www.omg.org/spec/UML/20131001">',
    '  <xmi:Documentation exporter="Modeling" exporterVersion="1.0"/>',
    '  <uml:Model xmi:type="uml:Model" name="CM_Model">',
    '    <packagedElement xmlns:xmi="http://www.omg.org/spec/XMI/20131001" '
    f'name="{escape(PACKAGE, {chr(34): "&quot;"})}" xmi:id="{package_id}" xmi:type="uml:Package">',
    *[element("Actor", code, title) for code, title in ACTORS],
    *[element("UseCase", code, title) for code, title in USE_CASES],
    '    </packagedElement>',
    '  </uml:Model>',
    '</xmi:XMI>',
]
OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
