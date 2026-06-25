from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from html import escape as xml_escape
from io import BytesIO
import zipfile


@dataclass(frozen=True)
class ExportTable:
    title: str
    subtitle: str
    headers: list[str]
    rows: list[list[str | Decimal]]
    footer_rows: list[list[str | Decimal]]
    sheet_name: str = "Report"


def text_value(value: str | Decimal) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return value


def column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xlsx_cell(row_index: int, column_index: int, value: str | Decimal, style: int | None = None) -> str:
    ref = f"{column_letter(column_index)}{row_index}"
    style_attr = f' s="{style}"' if style is not None else ""
    if isinstance(value, Decimal):
        return f'<c r="{ref}"{style_attr}><v>{value:.2f}</v></c>'
    return (
        f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{xml_escape(value)}</t></is></c>'
    )


def xlsx_row(row_index: int, values: Iterable[str | Decimal], style: int | None = None) -> str:
    cells = "".join(xlsx_cell(row_index, index, value, style) for index, value in enumerate(values, start=1))
    return f'<row r="{row_index}">{cells}</row>'


def build_xlsx(table: ExportTable) -> bytes:
    rows: list[str] = [
        xlsx_row(1, [table.title], 1),
        xlsx_row(2, [table.subtitle]),
        xlsx_row(4, table.headers, 1),
    ]
    current_row = 5
    for row in table.rows:
        rows.append(xlsx_row(current_row, row))
        current_row += 1
    current_row += 1
    for row in table.footer_rows:
        rows.append(xlsx_row(current_row, row, 1))
        current_row += 1

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetData>{''.join(rows)}</sheetData>
</worksheet>"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2"><xf fontId="0" fillId="0" borderId="0"/><xf fontId="1" fillId="0" borderId="0" applyFont="1"/></cellXfs>
</styleSheet>"""

    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
        )
        workbook.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        workbook.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="{xml_escape(table.sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
        )
        workbook.writestr("xl/styles.xml", styles_xml)
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return output.getvalue()


def safe_sheet_name(name: str, fallback: str) -> str:
    cleaned = "".join("_" if char in "[]:*?/\\'" else char for char in name).strip()
    return (cleaned or fallback)[:31]


def xlsx_styled_row(
    row_index: int,
    values: Iterable[str | Decimal],
    *,
    text_style: int | None = None,
    decimal_style: int | None = None,
    height: int | None = None,
) -> str:
    height_attr = f' ht="{height}" customHeight="1"' if height is not None else ""
    cells = "".join(
        xlsx_cell(
            row_index,
            index,
            value,
            decimal_style if isinstance(value, Decimal) else text_style,
        )
        for index, value in enumerate(values, start=1)
    )
    return f'<row r="{row_index}"{height_attr}>{cells}</row>'


def xlsx_columns_xml(table: ExportTable) -> str:
    column_count = max(
        [len(table.headers), *(len(row) for row in table.rows), *(len(row) for row in table.footer_rows)],
        default=1,
    )
    widths: list[str] = []
    source_rows = [table.headers, *table.rows[:80], *table.footer_rows]
    for column_index in range(column_count):
        max_length = 8
        for row in source_rows:
            if column_index < len(row):
                max_length = max(max_length, len(text_value(row[column_index])))
        width = min(max(max_length + 2, 10), 34)
        widths.append(
            f'<col min="{column_index + 1}" max="{column_index + 1}" width="{width}" customWidth="1"/>'
        )
    return f"<cols>{''.join(widths)}</cols>"


def xlsx_sheet_xml(table: ExportTable) -> str:
    rows: list[str] = [
        xlsx_styled_row(1, [table.title], text_style=2, height=18),
        xlsx_styled_row(2, [table.subtitle], text_style=5),
        xlsx_styled_row(4, table.headers, text_style=1, height=16),
    ]
    current_row = 5
    for row in table.rows:
        rows.append(xlsx_styled_row(current_row, row, decimal_style=3))
        current_row += 1
    current_row += 1
    for row in table.footer_rows:
        rows.append(xlsx_styled_row(current_row, row, text_style=1, decimal_style=4, height=16))
        current_row += 1

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="14"/>
  {xlsx_columns_xml(table)}
  <sheetData>{''.join(rows)}</sheetData>
  <autoFilter ref="A4:{column_letter(max(len(table.headers), 1))}4"/>
  <pageMargins left="0.3" right="0.3" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>
</worksheet>"""


def build_multi_sheet_xlsx(tables: list[ExportTable]) -> bytes:
    if not tables:
        raise ValueError("At least one export table is required.")

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3"><font><sz val="9"/><name val="Calibri"/></font><font><b/><sz val="9"/><name val="Calibri"/></font><font><b/><sz val="12"/><name val="Calibri"/></font></fonts>
  <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFEAF3EF"/><bgColor indexed="64"/></patternFill></fill></fills>
  <borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFD9E2E8"/></left><right style="thin"><color rgb="FFD9E2E8"/></right><top style="thin"><color rgb="FFD9E2E8"/></top><bottom style="thin"><color rgb="FFD9E2E8"/></bottom><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="6"><xf fontId="0" fillId="0" borderId="0"/><xf fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1"/><xf fontId="2" fillId="0" borderId="0" applyFont="1"/><xf fontId="0" fillId="0" borderId="0" numFmtId="4" applyNumberFormat="1"/><xf fontId="1" fillId="2" borderId="1" numFmtId="4" applyFont="1" applyFill="1" applyBorder="1" applyNumberFormat="1"/><xf fontId="0" fillId="0" borderId="0" applyFont="1"><alignment wrapText="1"/></xf></cellXfs>
</styleSheet>"""

    sheet_overrides = "\n".join(
        f'  <Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index, _ in enumerate(tables, start=1)
    )
    sheet_entries = "\n".join(
        f'    <sheet name="{xml_escape(safe_sheet_name(table.sheet_name, f"Sheet {index}"))}" sheetId="{index}" r:id="rId{index}"/>'
        for index, table in enumerate(tables, start=1)
    )
    sheet_relationships = "\n".join(
        f'  <Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index, _ in enumerate(tables, start=1)
    )
    styles_relationship_id = len(tables) + 1

    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{sheet_overrides}
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
        )
        workbook.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        workbook.writestr(
            "xl/workbook.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
{sheet_entries}
  </sheets>
</workbook>""",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{sheet_relationships}
  <Relationship Id="rId{styles_relationship_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
        )
        workbook.writestr("xl/styles.xml", styles_xml)
        for index, table in enumerate(tables, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", xlsx_sheet_xml(table))
    return output.getvalue()


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(table: ExportTable) -> bytes:
    lines = [table.title, table.subtitle, "", " | ".join(table.headers)]
    lines.extend(" | ".join(text_value(value) for value in row) for row in table.rows)
    lines.append("")
    lines.extend(" | ".join(text_value(value) for value in row) for row in table.footer_rows)

    y = 780
    commands = ["BT", "/F1 10 Tf"]
    for line in lines[:58]:
        commands.append(f"50 {y} Td ({pdf_escape(line[:115])}) Tj")
        commands.append(f"-50 -14 Td")
        y -= 14
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\n".encode())
        output.write(obj)
        output.write(b"\nendobj\n")
    xref = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for offset in offsets:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return output.getvalue()
