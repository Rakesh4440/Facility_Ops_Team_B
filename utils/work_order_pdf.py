"""Generate print-ready PDFs for individual maintenance work orders."""

from datetime import datetime
from textwrap import wrap


LEFT_MARGIN = 54
LINE_HEIGHT = 15
PAGE_BOTTOM = 72


def _pdf_text(value: object) -> str:
    """Return text that is safe for a PDF's built-in Helvetica font."""
    text = str(value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def _wrap(value: object, width: int = 78) -> list[str]:
    """Split long field values into readable PDF lines."""
    lines: list[str] = []
    for paragraph in str(value or "Not specified").splitlines() or ["Not specified"]:
        lines.extend(wrap(paragraph, width=width, break_long_words=True) or [""])
    return lines


def _work_kind(issue: str) -> tuple[str, str]:
    """Classify the work order and extract a schedule ID when present."""
    text = str(issue or "")
    if text.startswith("Preventive maintenance"):
        schedule_id = "Not linked"
        if "[" in text and "]" in text:
            schedule_id = text.split("[", 1)[1].split("]", 1)[0]
        return "Preventive (from schedule)", schedule_id
    return "Reactive (from machine failure)", "Not applicable"


def build_work_order_pdf(work_order: dict[str, object]) -> bytes:
    """Build a self-contained PDF handoff sheet for one work order."""
    prepared_at = datetime.now().strftime("%d %b %Y, %I:%M %p")
    kind, schedule_id = _work_kind(str(work_order.get("Issue", "")))
    sections = [
        ("DOCUMENT", [
            f"Document type: FacilityOps maintenance work-order handoff",
            f"Prepared on: {prepared_at}",
            f"Work order ID: {work_order['ID']}",
            f"Work kind: {kind}",
            f"Linked schedule ID: {schedule_id}",
        ]),
        ("ASSET", [
            f"Product ID: {work_order['Product ID']}",
            f"Machine type: {work_order['Machine Type']}",
            "Location / line: Confirm at the machine before work starts",
        ]),
        ("MAINTENANCE TASK", [
            f"Issue / work details: {work_order['Issue']}",
            "Objective: Restore safe, reliable operation and record the outcome.",
        ]),
        ("ASSIGNMENT & SCHEDULE", [
            f"Priority: {work_order['Priority']}",
            f"Assigned technician: {work_order['Assigned To']}",
            f"Due date: {work_order['Due Date']}",
            f"Current status: {work_order['Status']}",
        ]),
        ("SAFETY & PPE", [
            "1. Isolate energy sources and verify lockout/tagout before opening covers.",
            "2. Wear required PPE: safety glasses, gloves, and hearing protection as needed.",
            "3. Keep the area clear of unauthorized personnel during the repair.",
            "4. Stop work and escalate if an unsafe condition is found.",
        ]),
        ("SUGGESTED WORK STEPS", [
            "1. Confirm the asset ID and review the issue description on this sheet.",
            "2. Inspect the machine condition and note any abnormal readings or damage.",
            "3. Complete the repair, inspection, or safety check described above.",
            "4. Run a short functional check and clean the work area.",
            "5. Update the work-order status in FacilityOps when finished.",
        ]),
        ("TECHNICIAN HANDOFF", [
            "Review the machine condition before work begins. Complete the repair or "
            "inspection, follow site safety procedures, and update the work-order status "
            "when finished. Return spare parts or scrap to the designated store.",
        ]),
        ("COMPLETION RECORD", [
            "Work started (date/time): ______________________________",
            "Work finished (date/time): _____________________________",
            "Parts used / replaced: _________________________________",
            "Completion notes: ______________________________________",
            "Technician signature: __________________________________",
            "Supervisor signature: __________________________________",
        ]),
    ]

    pages_commands: list[list[str]] = []
    commands: list[str] = []
    y = 0

    def start_page() -> None:
        nonlocal commands, y
        commands = [
            "q", "0.05 0.20 0.35 rg", "0 792 595 50 re f", "Q",
            "BT", "/F2 18 Tf", "1 1 1 rg", f"{LEFT_MARGIN} 805 Td",
            "(FACILITYOPS MAINTENANCE WORK ORDER) Tj", "ET",
        ]
        y = 755

    def finish_page() -> None:
        commands.extend([
            "BT", "/F1 8 Tf", "0.35 0.35 0.35 rg", f"{LEFT_MARGIN} 40 Td",
            f"(FacilityOps AI Dashboard  |  Prepared {prepared_at}  |  Page {len(pages_commands) + 1}) Tj",
            "ET",
        ])
        pages_commands.append(commands)

    def ensure_space(needed: int) -> None:
        nonlocal y
        if y - needed < PAGE_BOTTOM:
            finish_page()
            start_page()

    start_page()
    for heading, fields in sections:
        ensure_space(40)
        commands.extend([
            "BT", "/F2 11 Tf", "0.05 0.20 0.35 rg", f"{LEFT_MARGIN} {y} Td",
            f"({_pdf_text(heading)}) Tj", "ET",
        ])
        y -= 20
        for field in fields:
            for line in _wrap(field):
                ensure_space(LINE_HEIGHT + 2)
                commands.extend([
                    "BT", "/F1 10 Tf", "0.12 0.12 0.12 rg", f"{LEFT_MARGIN} {y} Td",
                    f"({_pdf_text(line)}) Tj", "ET",
                ])
                y -= LINE_HEIGHT
        y -= 10

    finish_page()

    content_objects: list[bytes] = []
    page_objects: list[bytes] = []
    for page_commands in pages_commands:
        content = "\n".join(page_commands).encode("latin-1")
        content_objects.append(
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
        )

    # Object layout: 1 Catalog, 2 Pages, 3..N+2 Page, N+3 Font1, N+4 Font2, then contents
    page_count = len(pages_commands)
    font1_id = 3 + page_count
    font2_id = 4 + page_count
    first_content_id = 5 + page_count

    for index in range(page_count):
        content_id = first_content_id + index
        page_objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
        )

    kids = " ".join(f"{3 + i} 0 R" for i in range(page_count))
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode(),
        *page_objects,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        *content_objects,
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(pdf)
