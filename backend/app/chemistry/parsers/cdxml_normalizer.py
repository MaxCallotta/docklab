"""CDXML 结构规范化：合并 ChemDraw 片段标签，避免被拆成多个分子。

ChemDraw 会把 CO2H 等常用片段写成嵌套 <fragment>，并通过
ExternalConnectionPoint 连接回母体原子。OpenBabel 3.x 默认会将这类文件
解析成多个独立分子，导致配体不完整或生成空 PDBQT。
本模块在交给 OpenBabel 前，先把嵌套片段并入母体片段。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _build_parent_map(root: ET.Element) -> dict[ET.Element, ET.Element | None]:
    """记录每个 XML 节点的父节点，供向上查找所属 fragment 使用。"""

    parents: dict[ET.Element, ET.Element | None] = {root: None}
    for parent in root.iter():
        for child in parent:
            parents[child] = parent
    return parents


def _merge_fragment_node(
    node: ET.Element,
    parent_map: dict[ET.Element, ET.Element | None],
) -> bool:
    """将 n[NodeType=Fragment] 内的嵌套片段并入所属 fragment。"""

    nested = node.find("fragment")
    if nested is None:
        return False

    parent_fragment = parent_map[node]
    while parent_fragment is not None and parent_fragment.tag != "fragment":
        parent_fragment = parent_map[parent_fragment]
    if parent_fragment is None:
        return False

    node_id = node.get("id")
    if not node_id:
        return False

    ext_atom = next(
        (
            atom
            for atom in nested.findall("n")
            if atom.get("NodeType") == "ExternalConnectionPoint"
        ),
        None,
    )
    if ext_atom is None:
        return False
    ext_id = ext_atom.get("id")

    root_id: str | None = None
    ext_bond: ET.Element | None = None
    for bond in nested.findall("b"):
        if bond.get("B") == ext_id:
            root_id, ext_bond = bond.get("E"), bond
            break
        if bond.get("E") == ext_id:
            root_id, ext_bond = bond.get("B"), bond
            break
    if not root_id or ext_bond is None:
        return False

    # 外部连接点通常与母体原子完全重叠；找不到时回退到母体片段中
    # 与片段节点直接成键的原子。
    parent_atom_id: str | None = None
    ext_pos = (ext_atom.get("p") or "").strip()
    for atom in parent_fragment.findall("n"):
        if atom.get("id") != node_id and (atom.get("p") or "").strip() == ext_pos:
            parent_atom_id = atom.get("id")
            break
    if parent_atom_id is None:
        for bond in parent_fragment.findall("b"):
            if bond.get("B") == node_id:
                parent_atom_id = bond.get("E")
                break
            if bond.get("E") == node_id:
                parent_atom_id = bond.get("B")
                break
    if parent_atom_id is None:
        return False

    # 删除指向虚拟片段节点的母体键，并把片段自身的外部连接键改连到母体原子。
    for bond in list(parent_fragment.findall("b")):
        if bond.get("B") == node_id or bond.get("E") == node_id:
            parent_fragment.remove(bond)
    if ext_bond.get("B") == ext_id:
        ext_bond.set("B", parent_atom_id)
    else:
        ext_bond.set("E", parent_atom_id)

    # 把嵌套片段的原子与键移入母体片段，随后删除片段节点本身。
    for atom in list(nested.findall("n")):
        if atom.get("NodeType") == "ExternalConnectionPoint":
            continue
        parent_fragment.append(atom)
    for bond in list(nested.findall("b")):
        parent_fragment.append(bond)
    parent_fragment.remove(node)
    return True


def normalize_cdxml(source: Path, dest: Path) -> tuple[Path, bool]:
    """规范化 CDXML：合并嵌套片段，返回 (输出路径, 是否发生合并)。"""

    tree = ET.parse(source)
    root = tree.getroot()
    parent_map = _build_parent_map(root)
    nodes = [
        node
        for node in root.iter("n")
        if node.get("NodeType") == "Fragment" and node.find("fragment") is not None
    ]

    changed = False
    # 先处理深层节点，避免外层合并时引用已移动的元素。
    for node in reversed(nodes):
        changed = _merge_fragment_node(node, parent_map) or changed

    if not changed:
        dest.write_bytes(source.read_bytes())
        return dest, False

    tree.write(dest, encoding="UTF-8", xml_declaration=True)
    return dest, True
