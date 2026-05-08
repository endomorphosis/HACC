from __future__ import annotations

import re
import textwrap
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "Collateral Estoppel" / "drafts" / "print_build_2026-04-27"
OUT = OUT_DIR / "probate_sanctions_exhibits_binder_2026-04-27.pdf"
INDEX_MD = OUT_DIR / "probate_sanctions_exhibits_binder_index_2026-04-27.md"

PAGE_W, PAGE_H = letter
LEFT = RIGHT = 0.85 * inch
TOP = 0.8 * inch
BOTTOM = 0.65 * inch
BODY_FONT = "Times-Roman"
BOLD_FONT = "Times-Bold"
SIZE = 11
LINE_H = 14


EXHIBITS = [
    {
        "label": "Exhibit 1",
        "title": "First Amended Guardianship Petition",
        "purpose": "Source pleading challenged by the objection and ORCP 17 sanctions motion.",
        "files": [
            "evidence/history/Solomon Motion for Guardianship.pdf",
            "Collateral Estoppel/evidence_notes/solomon_motion_for_guardianship_ocr.txt",
        ],
    },
    {
        "label": "Exhibit 2",
        "title": "Writ of Assistance Materials",
        "purpose": "Shows the coercive relief requested or obtained through the probate proceeding.",
        "files": [
            "evidence/paper documents/writ of assistance solomon barber.pdf",
            "workspace/writ_of_assistance_solomon_barber_ocr.txt",
        ],
    },
    {
        "label": "Exhibit 3",
        "title": "Restraining Order Materials, Case No. 25PO11530",
        "purpose": "Shows the protective-order context omitted from the probate petition.",
        "files": [
            "evidence/history/sam barber restraining order.pdf",
            "Collateral Estoppel/evidence_notes/solomon_order_digest.md",
        ],
    },
    {
        "label": "Exhibit 4",
        "title": "Probate Petition False-Allegation Matrix",
        "purpose": "Maps petition allegations to contested proof issues and impeachment categories.",
        "files": [
            "Collateral Estoppel/drafts/motion_3_probate_petition_false_allegation_matrix_2026-04-26.md",
        ],
    },
    {
        "label": "Exhibit 5",
        "title": "Google Voice / Google Takeout Impeachment Materials",
        "purpose": "Summarizes Solomon's own statements relevant to notice, service, compliance, motive, and collateral attack.",
        "files": [
            "Collateral Estoppel/evidence_notes/solomon_google_voice_text_impeachment_exhibit_matrix_2026-04-26.md",
            "Collateral Estoppel/evidence_notes/solomon_probate_allegations_vs_google_voice_knowledge_comparison_2026-04-26.md",
        ],
    },
    {
        "label": "Exhibit 6",
        "title": "HACC / Quantum and Household-Composition Materials",
        "purpose": "Supports the disputed housing-causation and lease-removal issues.",
        "files": [
            "Collateral Estoppel/evidence_notes/delay_apportionment_timeline_solomon_vs_quantum_2026-04-07.md",
            "Collateral Estoppel/evidence_notes/jc_household_chain_household_composition_findings_2026-04-07.md",
            "Collateral Estoppel/evidence_notes/household_submission_and_participation_chronology_2026-04-09.md",
        ],
    },
    {
        "label": "Exhibit 7",
        "title": "Jane and Benjamin Declaration Materials",
        "purpose": "Supports residence history, relationship, inspection, lease-removal, and Jane's position.",
        "files": [
            "Collateral Estoppel/drafts/final_filing_set/04_declaration_of_benjamin_barber_in_support_of_motions_final.md",
            "Collateral Estoppel/evidence_notes/jane_cortez_declaration_april_8_2026_ocr.txt",
            "workspace/declaration_of_jane_cortez_march_23_2026_inspection_court_ready.md",
            "workspace/declaration_of_benjamin_barber_march_23_2026_inspection_court_ready.md",
        ],
    },
    {
        "label": "Exhibit 8",
        "title": "Trust / Inheritance Materials",
        "purpose": "Supports the objection that no-alternative and estate-value allegations require source proof.",
        "files": [
            "evidence/paper documents/Gerald miller jane cortez trust.pdf",
        ],
    },
    {
        "label": "Exhibit 9",
        "title": "Sanctions Exhibit Readiness Review",
        "purpose": "Identifies which allegations are ready for proof and which require supplementation.",
        "files": [
            "Collateral Estoppel/evidence_notes/motion_3_sanctions_exhibit_readiness_review_2026-04-26.md",
        ],
    },
    {
        "label": "Exhibit 10",
        "title": "University Place Hotel Reservation",
        "purpose": "Supports a concrete less-restrictive short-term housing alternative.",
        "files": [
            "evidence/paper documents/Gmail - Reservation Confirmation for Benjamin Barber Checking In_ 2026-04-30.pdf",
        ],
    },
]


def clean_md(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2610", "[ ]")
    return text


def wrap_line(line: str, width: float, font: str = BODY_FONT, size: int = SIZE) -> list[str]:
    if not line:
        return [""]
    words = line.split()
    out: list[str] = []
    cur = ""
    for word in words:
        test = word if not cur else f"{cur} {word}"
        if stringWidth(test, font, size) <= width:
            cur = test
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out or [""]


def draw_footer(c: canvas.Canvas, label: str, page_no: int) -> None:
    c.setFont(BODY_FONT, 8)
    c.drawString(LEFT, 0.38 * inch, label[:80])
    c.drawRightString(PAGE_W - RIGHT, 0.38 * inch, f"Page {page_no}")


def render_text_pdf(dest: Path, title: str, body: str, footer: str) -> None:
    c = canvas.Canvas(str(dest), pagesize=letter)
    y = PAGE_H - TOP
    page_no = 1
    draw_footer(c, footer, page_no)

    def new_page() -> None:
        nonlocal y, page_no
        c.showPage()
        page_no += 1
        y = PAGE_H - TOP
        draw_footer(c, footer, page_no)

    def line(text: str = "", font: str = BODY_FONT, size: int = SIZE, leading: int = LINE_H) -> None:
        nonlocal y
        if y < BOTTOM + leading:
            new_page()
        c.setFont(font, size)
        c.drawString(LEFT, y, text)
        y -= leading

    for part in wrap_line(title.upper(), PAGE_W - LEFT - RIGHT, BOLD_FONT, 13):
        line(part, BOLD_FONT, 13, 18)
    line()

    for raw in clean_md(body).splitlines():
        stripped = raw.strip()
        if not stripped:
            y -= 6
            continue
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().upper()
            y -= 4
            for part in wrap_line(heading, PAGE_W - LEFT - RIGHT, BOLD_FONT, 11):
                line(part, BOLD_FONT, 11, 15)
            continue
        indent = 0.2 * inch if stripped.startswith(("-", ">", "*")) else 0
        prefix = ""
        if stripped.startswith(">"):
            stripped = stripped.lstrip("> ").strip()
            prefix = '"'
        for i, part in enumerate(wrap_line(stripped, PAGE_W - LEFT - RIGHT - indent)):
            if y < BOTTOM + LINE_H:
                new_page()
            c.setFont(BODY_FONT, SIZE)
            c.drawString(LEFT + indent, y, (prefix if i == 0 else "") + part)
            y -= LINE_H
    c.save()


def cover_pdf(dest: Path, label: str, title: str, purpose: str, files: list[str]) -> None:
    body = "\n".join(
        [
            f"{label}",
            "",
            title,
            "",
            "Purpose:",
            purpose,
            "",
            "Source files included:",
            *[f"- {f}" for f in files],
        ]
    )
    render_text_pdf(dest, f"{label}: {title}", body, label)


def append_pdf(writer: PdfWriter, path: Path) -> int:
    reader = PdfReader(str(path))
    for page in reader.pages:
        writer.add_page(page)
    return len(reader.pages)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    manifest: list[tuple[str, str, int, str]] = []
    missing: list[str] = []

    with tempfile.TemporaryDirectory() as tmp_s:
        tmp = Path(tmp_s)

        index_lines = [
            "# Exhibit Binder Index",
            "",
            "Case No. 26PR00641",
            "In the Matter of Jane Kay Cortez",
            "Objector Benjamin Barber",
            "Prepared April 27, 2026",
            "",
        ]
        for ex in EXHIBITS:
            index_lines.append(f"- {ex['label']}: {ex['title']}")
        index = tmp / "00_index.pdf"
        render_text_pdf(index, "Exhibit Binder Index", "\n".join(index_lines), "EXHIBIT BINDER INDEX - 26PR00641")
        append_pdf(writer, index)

        for ex in EXHIBITS:
            cover = tmp / f"{ex['label'].replace(' ', '_')}_cover.pdf"
            cover_pdf(cover, ex["label"], ex["title"], ex["purpose"], ex["files"])
            added = append_pdf(writer, cover)
            page_count = added
            for rel in ex["files"]:
                path = ROOT / rel
                if not path.exists():
                    missing.append(rel)
                    continue
                if path.suffix.lower() == ".pdf":
                    page_count += append_pdf(writer, path)
                else:
                    rendered = tmp / f"{ex['label'].replace(' ', '_')}_{len(manifest)}.pdf"
                    body = path.read_text(encoding="utf-8", errors="replace")
                    render_text_pdf(rendered, path.name, body, f"{ex['label']} - {path.name}")
                    page_count += append_pdf(writer, rendered)
            manifest.append((ex["label"], ex["title"], page_count, "; ".join(ex["files"])))

    with OUT.open("wb") as f:
        writer.write(f)

    lines = [
        "# Probate Sanctions Exhibits Binder Index",
        "",
        "Case No. 26PR00641",
        "In the Matter of Jane Kay Cortez",
        "Objector Benjamin Barber",
        "Prepared April 27, 2026",
        "",
        "| Exhibit | Title | Binder pages | Source files |",
        "|---|---:|---:|---|".replace("---:", "---"),
    ]
    for label, title, pages, files in manifest:
        lines.append(f"| {label} | {title} | {pages} | {files} |")
    if missing:
        lines.extend(["", "## Missing source files", "", *[f"- {m}" for m in missing]])
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
