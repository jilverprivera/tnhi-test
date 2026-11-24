"""Genera el set de evaluación ciego (tests/blind).

Uso:  cd api && uv run python tests/blind/generar.py

Construye 60 correos .eml (emails/bNN.eml) y esperado-ciego.csv.
Las respuestas esperadas se derivan SOLO de las reglas de la entrevista con
Martha (material/1-entrevista), del maestro de proveedores y del libro de
radicación 2026; no del código del sistema.
"""

from __future__ import annotations

import csv
import io
import random
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path

from docx import Document
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent
EMAILS = OUT / "emails"
TZ = timezone(timedelta(hours=-5))
MAILBOX = "radicacion@terminalesandinas.example"
random.seed(20261118)

# --------------------------------------------------------------------------
# Calendario
# --------------------------------------------------------------------------
HOLIDAYS = {
    date(2026, 11, 2),
    date(2026, 11, 16),
    date(2026, 12, 8),
    date(2026, 12, 25),
    date(2027, 1, 1),
    date(2027, 1, 11),
}


def is_business(d: date) -> bool:
    return d.weekday() < 5 and d not in HOLIDAYS


def add_business(received: date, n: int) -> date:
    """n días hábiles contados desde el día hábil siguiente a la recepción."""
    d, count = received, 0
    while count < n:
        d += timedelta(days=1)
        if is_business(d):
            count += 1
    return d


def add_calendar(received: date, n: int) -> date:
    return received + timedelta(days=n)


# --------------------------------------------------------------------------
# Maestro (copia de los datos necesarios)
# --------------------------------------------------------------------------
SUP = {
    "llano": dict(
        nit="901.234.567-1",
        name="Suministros Industriales del Llano S.A.S.",
        mail="facturacion@suministrosllano.example",
        bank="Banco de Bogotá",
        acct_type="Corriente",
        acct="123-45678-9",
    ),
    "ferre": dict(
        nit="830.456.789-2",
        name="Ferretería y Eléctricos La 13 Ltda.",
        mail="ventas@ferrela13.example",
        bank="Davivienda",
        acct_type="Ahorros",
        acct="4567-0012-3456",
    ),
    "sabana": dict(
        nit="900.876.543-5",
        name="Transportes Sabana Express S.A.S.",
        mail="cartera@sabanaexpress.example",
        bank="Bancolombia",
        acct_type="Corriente",
        acct="245-000123-45",
    ),
    "aseo": dict(
        nit="901.112.233-4",
        name="Aseo Integral Bogotá S.A.S.",
        mail="facturacion@aseointegralbogota.example",
        bank="BBVA",
        acct_type="Corriente",
        acct="0013-0456-78-0100012345",
    ),
    "papel": dict(
        nit="860.555.444-3",
        name="Papelería y Suministros de Oficina Colombia S.A.",
        mail="fe@papeleriacolombia.example",
        bank="Banco de Occidente",
        acct_type="Ahorros",
        acct="987-65432-1",
    ),
    "lubri": dict(
        nit="900.333.222-8",
        name="Lubricantes y Combustibles de la Sabana S.A.S.",
        mail="facturas@lubrisabana.example",
        bank="Bancolombia",
        acct_type="Corriente",
        acct="310-998877-66",
    ),
    "vigi": dict(
        nit="800.777.666-1",
        name="Vigilancia Técnica Andina Ltda.",
        mail="contabilidad@vigiandina.example",
        bank="Banco Popular",
        acct_type="Corriente",
        acct="220-11122-3",
    ),
    "nube": dict(
        nit="901.999.000-7",
        name="Software Contable Nube S.A.S.",
        mail="facturacion@contablenube.example",
        bank="Bancolombia",
        acct_type="Ahorros",
        acct="540-332211-09",
    ),
    "monta": dict(
        nit="900.654.321-0",
        name="Mantenimiento de Montacargas El Puerto S.A.S.",
        mail="facturas@montacargaselpuerto.example",
        bank="Davivienda",
        acct_type="Corriente",
        acct="0550-7788-9911",
    ),
    "gloria": dict(
        nit="901.050.606-9",
        name="Servicios de Cafetería Doña Gloria S.A.S.",
        mail="gloria.cafeteria@cafeteriagloria.example",
        bank="Banco Caja Social",
        acct_type="Ahorros",
        acct="2400-556677",
    ),
}
TAC = "TERMINALES ANDINAS DE CARGA S.A. - NIT 900.100.200-3"

# --------------------------------------------------------------------------
# Generadores de adjuntos
# --------------------------------------------------------------------------


def _pdf_escape(s: str) -> bytes:
    b = s.encode("cp1252", errors="replace")
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def text_pdf(lines: list[str]) -> bytes:
    """PDF mínimo de una página, Helvetica, con texto real extraíble."""
    ops = [b"BT", b"/F2 13 Tf", b"50 750 Td", b"16 TL"]
    for i, ln in enumerate(lines):
        if i == 1:
            ops.append(b"/F1 10 Tf")
            ops.append(b"14 TL")
        ops.append(b"(" + _pdf_escape(ln) + b") '")
    ops.append(b"ET")
    stream = b"\n".join(ops)
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + o + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def _font(size: int):
    for p in (
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def scanned_pdf(lines: list[str]) -> bytes:
    """PDF de solo imagen (sin capa de texto) que simula un escaneo."""
    w, h = 1275, 1650  # carta a 150 dpi
    img = Image.new("L", (w, h), 248)
    d = ImageDraw.Draw(img)
    f_title, f_body = _font(34), _font(26)
    y = 90
    for i, ln in enumerate(lines):
        d.text(
            (80 + random.randint(-2, 2), y),
            ln,
            fill=random.randint(20, 60),
            font=f_title if i == 0 else f_body,
        )
        y += 48 if i == 0 else 38
    for _ in range(1500):  # ruido de escáner
        x, yy = random.randint(0, w - 1), random.randint(0, h - 1)
        d.point((x, yy), fill=random.randint(120, 200))
    img = img.rotate(random.uniform(-1.2, 1.2), fillcolor=245, resample=Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PDF", resolution=150.0)
    return buf.getvalue()


def docx_bytes(lines: list[str]) -> bytes:
    doc = Document()
    for i, ln in enumerate(lines):
        if i == 0:
            doc.add_heading(ln, level=1)
        else:
            doc.add_paragraph(ln)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def render(kind: str, lines: list[str]) -> tuple[bytes, str, str]:
    if kind == "pdf":
        return text_pdf(lines), "application", "pdf"
    if kind == "scan":
        return scanned_pdf(lines), "application", "pdf"
    if kind == "docx":
        return (
            docx_bytes(lines),
            "application",
            "vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    raise ValueError(kind)


# --------------------------------------------------------------------------
# Plantillas de contenido
# --------------------------------------------------------------------------


def invoice(
    s: dict,
    number: str,
    issued: str,
    items: list[tuple[str, int]],
    oc: str | None = None,
    acct: tuple[str, str, str] | None | bool = True,
    title="FACTURA ELECTRÓNICA DE VENTA",
    nit: str | None = None,
    name: str | None = None,
) -> list[str]:
    sub = sum(v for _, v in items)
    iva = round(sub * 0.19)
    lines = [
        f"{name or s['name']}",
        f"NIT {nit or s['nit']}",
        "",
        f"{title} No. {number}",
        f"Fecha de expedición: {issued}",
        f"Adquiriente: {TAC}",
        f"Orden de compra: {oc}" if oc else "Orden de compra: N/A",
        "",
        "Descripción                                   Valor",
    ]
    for desc, v in items:
        lines.append(f"{desc:<44} ${v:,.0f}".replace(",", "."))
    lines += [
        "",
        f"Subtotal: ${sub:,.0f}".replace(",", "."),
        f"IVA 19%: ${iva:,.0f}".replace(",", "."),
        f"TOTAL A PAGAR: ${sub + iva:,.0f}".replace(",", "."),
        "",
    ]
    if acct is True:
        lines.append(
            f"Favor consignar en {s['bank']}, cuenta {s['acct_type'].lower()} No. {s['acct']}"
        )
    elif acct:
        lines.append(f"Favor consignar en {acct[0]}, cuenta {acct[1]} No. {acct[2]}")
    lines.append("Forma de pago: crédito 30 días")
    return lines


def th_f_012(
    nombre, cc, cargo, area, destino, salida, regreso, motivo, valor, jefe, firmado: bool
) -> list[str]:
    return [
        "TERMINALES ANDINAS DE CARGA S.A.",
        "FORMATO TH-F-012  SOLICITUD DE VIÁTICOS Y GASTOS DE VIAJE  (Versión 3)",
        "",
        f"Nombre del funcionario: {nombre}",
        f"Cédula: {cc}",
        f"Cargo: {cargo}",
        f"Dependencia: {area}",
        f"Destino: {destino}",
        f"Fecha de salida: {salida}        Fecha de regreso: {regreso}",
        f"Motivo del viaje: {motivo}",
        f"Valor solicitado: {valor}",
        "",
        "APROBACIÓN DEL JEFE INMEDIATO",
        f"Nombre: {jefe if firmado else ''}",
        f"Firma: {'~~ ' + jefe.split()[-1] + ' ~~  (firmado)' if firmado else '______________________'}",
        f"Fecha de aprobación: {'ver fecha de envío' if firmado else '__________'}",
    ]


def oficio(entidad, num, ciudad_fecha, asunto, cuerpo: list[str], firma) -> list[str]:
    return (
        [
            entidad,
            "",
            f"Oficio No. {num}",
            ciudad_fecha,
            "",
            "Señores",
            "TERMINALES ANDINAS DE CARGA S.A.",
            "Representante legal",
            "",
            f"Asunto: {asunto}",
            "",
        ]
        + cuerpo
        + ["", "Atentamente,", "", firma]
    )


# --------------------------------------------------------------------------
# Casos
# --------------------------------------------------------------------------
CASES: list[dict] = []


def case(
    dt, frm, subject, body, atts=(), html=None, html_only=False, expected=(), to=MAILBOX, cc=None
):
    CASES.append(
        dict(
            dt=dt,
            frm=frm,
            subject=subject,
            body=body,
            atts=list(atts),
            html=html,
            html_only=html_only,
            expected=list(expected),
            to=to,
            cc=cc,
        )
    )


def D(day, hh, mm):
    return datetime(2026, 11, day, hh, mm, tzinfo=TZ)


def E(doc, tipo, dep, acc, obs, vence=None):
    return dict(documento=doc, tipo=tipo, dependencia=dep, accion=acc, vence=vence, observacion=obs)


FILE, RET, NOF, REP, HOLD = (
    "FILE",
    "RETURN_TO_SENDER",
    "DO_NOT_FILE",
    "REPLY_WITH_EXISTING_NUMBER",
    "HOLD_FOR_VERIFICATION",
)
INV, TRV, PET, OVS, CMP, QUO, ADV = (
    "INVOICE",
    "TRAVEL_EXPENSE_REQUEST",
    "PETITION",
    "OVERSIGHT_NOTICE",
    "COMPLAINT",
    "QUOTATION",
    "ADVERTISING",
)

# ============================== FACTURAS =================================
s = SUP["llano"]
case(
    D(3, 8, 40),
    f"Facturación Suministros del Llano <{s['mail']}>",
    "Factura electrónica FE-3402 Suministros Industriales del Llano",
    "Buenos días,\n\nRemitimos la factura electrónica FE-3402 por el suministro de guantes de nitrilo y "
    "tapabocas, según orden de compra OC-2026-0431.\n\nCordialmente,\nÁrea de facturación\n"
    + s["name"],
    [
        (
            "FE-3402.pdf",
            "pdf",
            invoice(
                s,
                "FE-3402",
                "2026-11-02",
                [
                    ("Guantes de nitrilo x 100 (20 cajas)", 1240000),
                    ("Tapabocas N95 x 50 (10 cajas)", 890000),
                ],
                oc="OC-2026-0431",
            ),
        )
    ],
    expected=[
        E(
            "FE-3402.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "Proveedor en el maestro (NIT 901.234.567-1), trae OC-2026-0431, cuenta y dominio coinciden",
        )
    ],
)

s = SUP["ferre"]
html = (
    "<html><body><p>Buenas tardes señores <b>TAC</b>,</p><p>Adjuntamos factura <b>FV-10571</b> "
    "por los materiales eléctricos que recogió el señor de mantenimiento el viernes.</p>"
    "<p>Cualquier inquietud con gusto.</p><p>--<br>Ventas<br>Ferretería y Eléctricos La 13</p></body></html>"
)
case(
    D(3, 15, 22),
    f"Ventas Ferretería La 13 <{s['mail']}>",
    "Factura FV-10571",
    "Buenas tardes señores TAC,\nAdjuntamos factura FV-10571 por los materiales eléctricos que recogió "
    "el señor de mantenimiento el viernes.\nCualquier inquietud con gusto.\n--\nVentas",
    html=html,
    atts=[
        (
            "FV-10571.pdf",
            "pdf",
            invoice(
                s,
                "FV-10571",
                "2026-10-30",
                [("Cable encauchetado 3x12 (50 m)", 410000), ("Breakers 2x30A (6 und)", 186000)],
            ),
        )
    ],
    expected=[
        E(
            "FV-10571.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor registrado pero la factura no trae orden de compra: Compras debe avalar",
        )
    ],
)

s = SUP["sabana"]
case(
    D(4, 9, 5),
    f"Cartera Sabana Express <{s['mail']}>",
    "COBRO PENDIENTE - factura vencida",
    "Señores Terminales Andinas,\n\nA la fecha no registramos el pago de la factura SE-77790 por el "
    "servicio de transporte de octubre. Adjuntamos nuevamente copia escaneada. Agradecemos programar el "
    "pago a la mayor brevedad.\n\nLuz Dary Cárdenas\nCartera",
    [
        (
            "Escaneo_SE77790.pdf",
            "scan",
            invoice(
                s,
                "SE-77790",
                "2026-10-28",
                [("Transporte contenedores Buenaventura-Funza (6 viajes)", 7058824)],
            ),
        )
    ],
    expected=[
        E(
            "Escaneo_SE77790.pdf",
            INV,
            "SENDER",
            REP,
            "Factura SE-77790 de Transportes Sabana ya radicada (TAC-2026-ER-04791): no se radica de nuevo, "
            "se responde con el radicado existente",
        )
    ],
)

s = SUP["aseo"]
case(
    D(5, 7, 31),
    f"Facturación Aseo Integral <{s['mail']}>",
    "RV: Factura servicio de aseo octubre AIB-2026-1102",
    "Buen día, reenviamos la factura AIB-2026-1102 pues no hemos recibido confirmación de pago.\n\n"
    "-----Mensaje original-----\nDe: "
    + s["mail"]
    + "\nEnviado: lunes, 2 de noviembre de 2026 4:12 p. m.\n"
    "Para: " + MAILBOX + "\nAsunto: Factura servicio de aseo octubre AIB-2026-1102\n\n"
    "Adjuntamos factura del servicio de aseo de octubre, OC-2026-0377.",
    [
        (
            "AIB-2026-1102.pdf",
            "pdf",
            invoice(
                s,
                "AIB-2026-1102",
                "2026-10-31",
                [("Servicio de aseo y cafetería octubre 2026", 6300000)],
                oc="OC-2026-0377",
            ),
        )
    ],
    expected=[
        E(
            "AIB-2026-1102.pdf",
            INV,
            "SENDER",
            REP,
            "Duplicado: AIB-2026-1102 de Aseo Integral ya está en el libro (TAC-2026-ER-04795); "
            "responder con ese radicado",
        )
    ],
)

s = SUP["nube"]
case(
    D(5, 11, 47),
    f"Facturación Contable Nube <{s['mail']}>",
    "Factura FE-1207 licenciamiento noviembre",
    "Estimado cliente,\n\nAdjuntamos su factura electrónica FE-1207 correspondiente al licenciamiento "
    "mensual del software contable (OC-2026-0455).\n\nEquipo de facturación\nSoftware Contable Nube S.A.S.",
    [
        (
            "FE-1207.pdf",
            "pdf",
            invoice(
                s,
                "FE-1207",
                "2026-11-01",
                [("Licencia ERP contable 15 usuarios - noviembre", 3150000)],
                oc="OC-2026-0455",
            ),
        )
    ],
    expected=[
        E(
            "FE-1207.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "FE-1207 existe en el libro pero de Papelería Colombia (otro NIT): no es duplicado. "
            "Proveedor registrado con OC-2026-0455",
        )
    ],
)

s = SUP["lubri"]
case(
    D(6, 16, 58),
    f"Facturas Lubrisabana <{s['mail']}>",
    "Facturas LS-20931 y LS-20932",
    "Señores TAC,\nremitimos dos facturas: la LS-20931 corresponde a la OC-2026-0440 (ACPM). "
    "La LS-20932 es del aceite hidráulico que nos pidieron por teléfono, esa no tiene orden.\n\n"
    "Lubricantes y Combustibles de la Sabana",
    [
        (
            "LS-20931.pdf",
            "pdf",
            invoice(
                s, "LS-20931", "2026-11-05", [("ACPM (2.000 galones)", 21800000)], oc="OC-2026-0440"
            ),
        ),
        (
            "LS-20932.pdf",
            "pdf",
            invoice(
                s, "LS-20932", "2026-11-05", [("Aceite hidráulico ISO 68 (4 canecas)", 2960000)]
            ),
        ),
    ],
    expected=[
        E("LS-20931.pdf", INV, "ACCOUNTS_PAYABLE", FILE, "Proveedor registrado, con OC-2026-0440"),
        E(
            "LS-20932.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor registrado sin orden de compra (pedido telefónico): a Compras",
        ),
    ],
)

s = SUP["vigi"]
case(
    D(9, 10, 12),
    f"Contabilidad Vigilancia Técnica Andina <{s['mail']}>",
    "Factura VTA-0988 servicio de vigilancia octubre",
    "Buenos días.\nAdjunto factura VTA-0988 del servicio de vigilancia de octubre, orden de compra "
    "OC-2026-0398.\nAtentamente,\nContabilidad",
    [
        (
            "VTA-0988.pdf",
            "pdf",
            invoice(
                s,
                "VTA-0988",
                "2026-11-03",
                [("Servicio de vigilancia 24h portería 2 - octubre", 9800000)],
                oc="OC-2026-0398",
            ),
        )
    ],
    expected=[
        E(
            "VTA-0988.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor en el maestro pero en estado INACTIVO: no se puede mandar a pago; "
            "Compras debe revisar/reactivar (criterio documentado en README)",
        )
    ],
)

s = SUP["monta"]
case(
    D(9, 14, 30),
    f"Facturas Montacargas El Puerto <{s['mail']}>",
    "Factura MP-5507 - ACTUALIZACION DATOS BANCARIOS",
    "Señores Terminales Andinas,\n\nAdjuntamos factura MP-5507 por el mantenimiento preventivo de los "
    "montacargas (OC-2026-0420).\nLes informamos que por cambio de entidad financiera, a partir de esta "
    "factura los pagos deben hacerse a la nueva cuenta indicada en el documento.\n\nCordialmente,\n"
    "Departamento de cartera",
    [
        (
            "MP-5507.pdf",
            "pdf",
            invoice(
                s,
                "MP-5507",
                "2026-11-06",
                [("Mantenimiento preventivo montacargas (4 und)", 5600000)],
                oc="OC-2026-0420",
                acct=("Banco Pichincha", "ahorros", "410-2233-8877"),
            ),
        )
    ],
    expected=[
        E(
            "MP-5507.pdf",
            INV,
            "ADMIN_COORDINATION",
            HOLD,
            "La cuenta de la factura (Banco Pichincha 410-2233-8877) no es la del maestro "
            "(Davivienda 0550-7788-9911): retener para verificación telefónica con la Dra. Claudia",
        )
    ],
)

s = SUP["llano"]
case(
    D(10, 8, 3),
    "Facturación Suministros del Llano <facturacion@suministros-llano.example>",
    "Factura electrónica FE-3415 - Suministros Industriales del Llano",
    "Buenos días,\n\nAdjuntamos la factura electrónica FE-3415 correspondiente a la orden de compra "
    "OC-2026-0431 (segunda entrega).\n\nCordialmente,\nÁrea de facturación\n" + s["name"],
    [
        (
            "FE-3415.pdf",
            "pdf",
            invoice(
                s,
                "FE-3415",
                "2026-11-09",
                [("Botas de seguridad dieléctricas (30 pares)", 4350000)],
                oc="OC-2026-0431",
            ),
        )
    ],
    expected=[
        E(
            "FE-3415.pdf",
            INV,
            "ADMIN_COORDINATION",
            HOLD,
            "Correo enviado desde suministros-llano.example (dominio parecido) y no desde "
            "suministrosllano.example del maestro: posible suplantación, verificar con el proveedor",
        )
    ],
)

s = SUP["sabana"]
case(
    D(11, 21, 40),
    "Cartera Sabana Express <cartera@sabanaexpres.example>",
    "Factura SE-77845 / nueva cuenta para pagos",
    "Buenas noches,\n\nRemitimos factura SE-77845. Por favor tener en cuenta que por políticas del banco "
    "nuestra cuenta Bancolombia fue cancelada; favor consignar en la cuenta de ahorros Nequi Empresas "
    "No. 301-554-7788.\n\nGracias,\nCartera Transportes Sabana Express",
    [
        (
            "SE-77845.pdf",
            "pdf",
            invoice(
                s,
                "SE-77845",
                "2026-11-10",
                [("Transporte de carga suelta Funza-Bogotá (3 viajes)", 3900000)],
                oc="OC-2026-0444",
                acct=("Nequi Empresas", "ahorros", "301-554-7788"),
            ),
        )
    ],
    expected=[
        E(
            "SE-77845.pdf",
            INV,
            "ADMIN_COORDINATION",
            HOLD,
            "Dominio sabanaexpres.example (falta una 's') y cuenta distinta a la del maestro: "
            "intento de fraude probable, a la Dra. Claudia",
        )
    ],
)

case(
    D(12, 12, 15),
    "Jhon Fredy Pardo <jhonfredy.pardo.pinturas@correoficticio.example>",
    "cuenta de cobro",
    "buenas tardes le envio la cuenta de cobro por la pintura de la señalizacion del patio 1 que me "
    "contrato el ingeniero de operaciones. quedo pendiente\n\nJhon Fredy Pardo\ncel 310 555 1234",
    [
        (
            "Cuenta de cobro 014.docx",
            "docx",
            [
                "CUENTA DE COBRO No. 014",
                "Bogotá, 11 de noviembre de 2026",
                "",
                "TERMINALES ANDINAS DE CARGA S.A.",
                "NIT 900.100.200-3",
                "",
                "DEBE A: Jhon Fredy Pardo Rincón, C.C. 80.123.456 de Bogotá",
                "La suma de: UN MILLÓN OCHOCIENTOS MIL PESOS ($1.800.000)",
                "Por concepto de: pintura de señalización horizontal patio 1 (demarcación de carriles y pasos peatonales).",
                "",
                "Declaro que no soy responsable de IVA.",
                "Favor consignar en cuenta de ahorros Bancolombia No. 091-778899-12 a mi nombre.",
                "",
                "Firma: Jhon Fredy Pardo R.",
                "C.C. 80.123.456",
            ],
        )
    ],
    expected=[
        E(
            "Cuenta de cobro 014.docx",
            INV,
            "PROCUREMENT",
            FILE,
            "Cuenta de cobro de persona natural (C.C. 80.123.456) que no está en el maestro: "
            "Compras debe vincularlo",
        )
    ],
)

case(
    D(13, 9, 44),
    "Facturación Grúas y Izajes Cundinamarca <facturacion@gruasizajescund.example>",
    "Factura GI-2210 servicio de grua",
    "Buenos días, enviamos factura GI-2210 por el servicio de grúa de 50 toneladas del 6 de noviembre, "
    "orden de compra OC-2026-0450 que nos enviaron.\n\nGrúas y Izajes Cundinamarca S.A.S.",
    [
        (
            "GI-2210.pdf",
            "pdf",
            invoice(
                dict(
                    nit="901.777.888-2",
                    name="Grúas y Izajes Cundinamarca S.A.S.",
                    bank="Banco AV Villas",
                    acct_type="Corriente",
                    acct="077-12345-6",
                ),
                "GI-2210",
                "2026-11-09",
                [("Servicio de grúa 50 t (8 horas)", 6400000)],
                oc="OC-2026-0450",
            ),
        )
    ],
    expected=[
        E(
            "GI-2210.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "NIT 901.777.888-2 no está en el maestro: va a Compras para vinculación aunque traiga OC",
        )
    ],
)

s = SUP["gloria"]
case(
    D(7, 10, 20),
    f"Cafeteria Doña Gloria <{s['mail']}>",
    "Cuenta de cobro octubre - refrigerios",
    "Buenos días doctora, le mando la cuenta de cobro de los refrigerios de octubre, corresponde a la "
    "OC-2026-0402. La escaneé porque la firmé a mano.\n\nGloria Amparo Suárez\nServicios de Cafetería Doña Gloria",
    [
        (
            "CamScanner 07-11-2026 10.18.pdf",
            "scan",
            invoice(
                s,
                "GL-0311",
                "2026-11-06",
                [("Refrigerios reuniones octubre (180 und)", 1620000)],
                acct=True,
                title="CUENTA DE COBRO",
            ),
        )
    ],
    expected=[
        E(
            "CamScanner 07-11-2026 10.18.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "Cuenta de cobro GL-0311 de proveedor registrado; la OC-2026-0402 viene en el correo; "
            "cuenta coincide con el maestro",
        )
    ],
)

s = SUP["papel"]
case(
    D(17, 8, 55),
    f"FE Papeleria Colombia <{s['mail']}>",
    "FACTURA ELECTRONICA FE1239 TERMINALES ANDINAS",
    "SEÑORES TERMINALES ANDINAS, ADJUNTO FACTURA ELECTRONICA FE-1239 SEGUN OC-2026-0461. GRACIAS.",
    [
        (
            "FE-1239.pdf",
            "pdf",
            invoice(
                s,
                "FE-1239",
                "2026-11-13",
                [("Resmas papel carta (40 und)", 640000), ("Tóner HP 26A (4 und)", 1480000)],
                oc="OC-2026-0461",
                nit="860555444-3",
            ),
        )
    ],
    expected=[
        E(
            "FE-1239.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "NIT 860555444-3 (sin puntos) = 860.555.444-3 del maestro; trae OC-2026-0461",
        )
    ],
)

s = SUP["ferre"]
case(
    D(11, 10, 30),
    "Cartera Ferretería La 13 <cartera@ferrela13.example>",
    "facturas pendientes de pago",
    "Buenos dias, de parte de cartera de Ferreteria La 13 les recordamos la factura FV-10498 que aun "
    "aparece sin pago (va escaneada con el recibido) y les enviamos la nueva FV-10580 de los "
    "reflectores.\nGracias",
    [
        (
            "FV-10498 recibido.pdf",
            "scan",
            invoice(s, "FV-10498", "2026-10-29", [("Tubería conduit 1/2 (40 und)", 617143)]),
        ),
        (
            "FV-10580.pdf",
            "pdf",
            invoice(s, "FV-10580", "2026-11-10", [("Reflectores LED 200W (8 und)", 1544000)]),
        ),
    ],
    expected=[
        E(
            "FV-10498 recibido.pdf",
            INV,
            "SENDER",
            REP,
            "FV-10498 de Ferretería La 13 ya radicada (TAC-2026-ER-04794): responder con ese radicado",
        ),
        E(
            "FV-10580.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor registrado, sin OC. Remitente cartera@ferrela13.example: mismo dominio del maestro",
        ),
    ],
)

s = SUP["aseo"]
html = (
    "<html><body><p>Estimados,</p><p>Adjuntamos dos facturas:</p><ul>"
    "<li>AIB-2026-1150 – servicio de aseo noviembre (primera quincena), OC-2026-0466</li>"
    "<li>AIB-2026-1151 – jornada extra de desinfección de bodegas solicitada por el jefe de patio</li>"
    "</ul><p>Departamento de facturación<br>Aseo Integral Bogotá S.A.S.</p></body></html>"
)
case(
    D(12, 17, 5),
    f"Facturación Aseo Integral <{s['mail']}>",
    "Facturas AIB-2026-1150 / AIB-2026-1151",
    "",
    html=html,
    html_only=True,
    atts=[
        (
            "AIB-2026-1150.pdf",
            "pdf",
            invoice(
                s,
                "AIB-2026-1150",
                "2026-11-12",
                [("Servicio de aseo 1a quincena noviembre", 3150000)],
                oc="OC-2026-0466",
            ),
        ),
        (
            "AIB-2026-1151.pdf",
            "pdf",
            invoice(
                s,
                "AIB-2026-1151",
                "2026-11-12",
                [("Jornada extra desinfección bodegas 3 y 4", 980000)],
            ),
        ),
    ],
    expected=[
        E(
            "AIB-2026-1150.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "Proveedor registrado con OC-2026-0466",
        ),
        E(
            "AIB-2026-1151.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor registrado, servicio pedido sin orden de compra",
        ),
    ],
)

case(
    D(15, 19, 22),
    "Soluciones Electricas JR <solelectricasjr@correoficticio.example>",
    "Cobro arreglo transformador",
    "Buenas noches, adjunto la cuenta de cobro CC-0087 del arreglo del transformador de la portería que "
    "hicimos el sábado de urgencia. Agradezco el pago pronto.\n\nRaúl Jiménez\nSoluciones Eléctricas JR",
    [
        (
            "CC-0087.pdf",
            "pdf",
            invoice(
                dict(
                    nit="1.020.345.678-9",
                    name="Soluciones Eléctricas JR",
                    bank="Davivienda",
                    acct_type="Ahorros",
                    acct="0570-1122-3344",
                ),
                "CC-0087",
                "2026-11-14",
                [("Reparación transformador portería", 2300000)],
                title="CUENTA DE COBRO",
            ),
        )
    ],
    expected=[
        E(
            "CC-0087.pdf",
            INV,
            "PROCUREMENT",
            FILE,
            "Proveedor no registrado (NIT 1.020.345.678-9 no está en el maestro): a Compras",
        )
    ],
)

s = SUP["monta"]
case(
    D(16, 9, 0),
    f"Facturas Montacargas El Puerto <{s['mail']}>",
    "Factura MP-5520",
    "Buenos días, remitimos factura MP-5520 por cambio de llantas montacargas No. 3, OC-2026-0420.\nCordialmente",
    [
        (
            "MP-5520.pdf",
            "pdf",
            invoice(
                s,
                "MP-5520",
                "2026-11-13",
                [("Llantas macizas montacargas (4 und)", 3720000)],
                oc="OC-2026-0420",
            ),
        )
    ],
    expected=[
        E(
            "MP-5520.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "Proveedor registrado, OC-2026-0420, cuenta Davivienda coincide (recibido en festivo, "
            "no afecta la ruta)",
        )
    ],
)

s = SUP["sabana"]
case(
    D(6, 13, 13),
    "Cartera Sabana Express <sabanaexpress.cartera@gmail.example>",
    "Factura SE-77860",
    "Buenas tardes, envío factura SE-77860 desde este correo porque el corporativo está con fallas. "
    "Corresponde a la OC-2026-0444.\nLuz Dary Cárdenas - Cartera",
    [
        (
            "SE-77860.pdf",
            "pdf",
            invoice(
                s,
                "SE-77860",
                "2026-11-05",
                [("Transporte contenedores Buenaventura-Funza (2 viajes)", 2352941)],
                oc="OC-2026-0444",
            ),
        )
    ],
    expected=[
        E(
            "SE-77860.pdf",
            INV,
            "ADMIN_COORDINATION",
            HOLD,
            "Llega desde gmail.example, no desde sabanaexpress.example del maestro (dirección rara), "
            "aunque la cuenta coincida: verificar",
        )
    ],
)

s = SUP["lubri"]
case(
    D(14, 22, 10),
    f"Facturas Lubrisabana <{s['mail']}>",
    "Envío factura electrónica LS-20950",
    "Señores TAC, remitimos la factura LS-20950 del despacho de grasa y ACPM, OC-2026-0449.\n"
    "Lubricantes y Combustibles de la Sabana",
    [
        (
            "LS-20950.pdf",
            "pdf",
            invoice(
                s,
                "LS-20950",
                "2026-11-14",
                [("ACPM (800 galones)", 8720000), ("Grasa EP2 (2 baldes)", 540000)],
                oc="OC-2026-0449",
            ),
        )
    ],
    expected=[
        E("LS-20950.pdf", INV, "ACCOUNTS_PAYABLE", FILE, "Proveedor registrado con OC-2026-0449")
    ],
)

s = SUP["papel"]
case(
    D(17, 16, 40),
    f"FE Papelería Colombia <{s['mail']}>",
    "Factura FE-1244 - datos de pago",
    "Buenas tardes,\nAdjuntamos factura FE-1244 (OC-2026-0461, saldo). Para este pago les solicitamos "
    "consignar a la cuenta corriente Bancolombia No. 112-908877-01, ya que la cuenta de Occidente está "
    "en proceso de cierre.\n\nGracias,\nFacturación electrónica",
    [
        (
            "FE-1244.pdf",
            "pdf",
            invoice(
                s,
                "FE-1244",
                "2026-11-17",
                [("Carpetas AZ (60 und)", 420000)],
                oc="OC-2026-0461",
                acct=None,
            ),
        )
    ],
    expected=[
        E(
            "FE-1244.pdf",
            INV,
            "ADMIN_COORDINATION",
            HOLD,
            "El correo pide pagar a una cuenta (Bancolombia 112-908877-01) distinta a la del maestro "
            "(Occidente 987-65432-1): retener para verificación",
        )
    ],
)

# ============================== VIÁTICOS =================================
case(
    D(4, 9, 30),
    "Camilo Andrés Restrepo <camilo.restrepo@terminalesandinas.example>",
    "Solicitud viáticos Buenaventura",
    "Martha buen día, adjunto el TH-F-012 firmado por el ingeniero Méndez para la visita al puerto de "
    "Buenaventura.\nGracias\nCamilo",
    [
        (
            "TH-F-012 Camilo Restrepo.pdf",
            "pdf",
            th_f_012(
                "Camilo Andrés Restrepo",
                "1.019.334.556",
                "Coordinador de patio",
                "Operaciones",
                "Buenaventura",
                "2026-11-23",
                "2026-11-25",
                "Reunión con operador portuario",
                "$1.260.000",
                "Ing. Carlos Méndez",
                True,
            ),
        )
    ],
    expected=[
        E(
            "TH-F-012 Camilo Restrepo.pdf",
            TRV,
            "HUMAN_RESOURCES",
            FILE,
            "Formato TH-F-012 con firma del jefe; llega el 4 nov para viaje el 23 nov (más de 5 días hábiles)",
        )
    ],
)

case(
    D(12, 15, 10),
    "Paola Andrea Niño <paola.nino@terminalesandinas.example>",
    "viaticos cartagena - URGENTE",
    "Martha, me salió el viaje de un momento a otro. Te adjunto el formato firmado por la doctora Claudia. "
    "Salgo el martes 17.\nPaola",
    [
        (
            "TH-F-012 Paola Nino.docx",
            "docx",
            th_f_012(
                "Paola Andrea Niño",
                "52.887.301",
                "Analista financiera",
                "Administrativa y financiera",
                "Cartagena",
                "2026-11-17",
                "2026-11-18",
                "Auditoría a proveedor de transporte",
                "$980.000",
                "Dra. Claudia Herrera",
                True,
            ),
        )
    ],
    expected=[
        E(
            "TH-F-012 Paola Nino.docx",
            TRV,
            "HUMAN_RESOURCES",
            FILE,
            "Formato completo y aprobado pero EXTEMPORÁNEA: llega el 12 nov para viaje el 17 nov "
            "(menos de 5 días hábiles; 16 nov festivo)",
        )
    ],
)

case(
    D(9, 8, 15),
    "Hernando Velásquez <hernando.velasquez@terminalesandinas.example>",
    "Viáticos Ipiales diciembre",
    "Hola Martha, necesito viáticos para ir a Ipiales del 9 al 11 de diciembre a la inspección de la "
    "frontera. Son 3 días, hotel y alimentación. Mi jefe ya sabe, él me dijo que te escribiera.\n\n"
    "Hernando Velásquez\nInspector de carga",
    expected=[
        E(
            "EMAIL_BODY",
            TRV,
            "SENDER",
            RET,
            "Solicitud en el cuerpo del correo, sin formato TH-F-012 ni aprobación del jefe: devolver",
        )
    ],
)

case(
    D(10, 10, 40),
    "Natalia Gómez <natalia.gomez@terminalesandinas.example>",
    "RV: aprobación viaje Medellín",
    "Martha, te reenvío el correo donde mi jefe me aprueba el viaje y te adjunto el formato. "
    "Él no alcanzó a firmarlo porque está en vacaciones.\n\n"
    "-----Mensaje original-----\nDe: Jorge Salamanca <jorge.salamanca@terminalesandinas.example>\n"
    "Enviado: lunes, 9 de noviembre de 2026 6:02 p. m.\nPara: Natalia Gómez\nAsunto: RE: viaje Medellín\n\n"
    "Aprobado Natalia, adelante con el viaje.\nJorge",
    [
        (
            "TH-F-012 Natalia Gomez.pdf",
            "pdf",
            th_f_012(
                "Natalia Gómez Ruiz",
                "1.036.221.908",
                "Analista de compras",
                "Compras y contratación",
                "Medellín",
                "2026-11-30",
                "2026-12-01",
                "Feria de proveedores logísticos",
                "$720.000",
                "Jorge Salamanca",
                False,
            ),
        )
    ],
    expected=[
        E(
            "TH-F-012 Natalia Gomez.pdf",
            TRV,
            "SENDER",
            RET,
            "El TH-F-012 no tiene firma/aprobación del jefe; la aprobación por correo no sustituye la "
            "firma en el formato (criterio README): devolver",
        )
    ],
)

case(
    D(14, 11, 5),
    "Yesid Murillo <yesid.murillo@terminalesandinas.example>",
    "formato viaticos",
    "buenos dias adjunto formato escaneado firmado por el jefe para el viaje a Santa Marta. gracias",
    [
        (
            "scan0001.pdf",
            "scan",
            th_f_012(
                "Yesid Murillo Palacios",
                "1.077.445.120",
                "Supervisor de báscula",
                "Operaciones",
                "Santa Marta",
                "2026-12-01",
                "2026-12-03",
                "Calibración báscula sede norte",
                "$1.450.000",
                "Ing. Carlos Méndez",
                True,
            ),
        )
    ],
    expected=[
        E(
            "scan0001.pdf",
            TRV,
            "HUMAN_RESOURCES",
            FILE,
            "TH-F-012 escaneado con firma del jefe; recibido el sábado 14 nov para viaje el 1 dic: a tiempo",
        )
    ],
)

case(
    D(13, 18, 20),
    "Sergio Lozano <sergio.lozano@terminalesandinas.example>",
    "Viáticos Bucaramanga",
    "Martha adjunto el formato, el jefe lo firma el lunes. Viajo el miércoles 18.",
    [
        (
            "TH-F-012 Sergio Lozano.pdf",
            "pdf",
            th_f_012(
                "Sergio Lozano Díaz",
                "91.502.334",
                "Técnico de mantenimiento",
                "Mantenimiento",
                "Bucaramanga",
                "2026-11-18",
                "2026-11-19",
                "Reparación de grúa en patio aliado",
                "$640.000",
                "Ing. Fabio Rueda",
                False,
            ),
        )
    ],
    expected=[
        E(
            "TH-F-012 Sergio Lozano.pdf",
            TRV,
            "SENDER",
            RET,
            "Formato sin firma del jefe: se devuelve (además sería extemporánea)",
        )
    ],
)

case(
    D(11, 14, 0),
    "Secretaría Operaciones <secretaria.operaciones@terminalesandinas.example>",
    "Solicitudes de viáticos operaciones - Barranquilla",
    "Martha buenas tardes, te envío los dos formatos de los compañeros que viajan a Barranquilla. El de "
    "Andrés ya está firmado por el ingeniero; el de Mónica falta la firma, el ingeniero lo firma mañana.\n\n"
    "Rocío\nSecretaría de Operaciones",
    [
        (
            "TH-F-012 Andres Cuervo.pdf",
            "pdf",
            th_f_012(
                "Andrés Cuervo Rincón",
                "80.765.432",
                "Jefe de turno",
                "Operaciones",
                "Barranquilla",
                "2026-11-30",
                "2026-12-02",
                "Capacitación sistema de turnos",
                "$1.150.000",
                "Ing. Carlos Méndez",
                True,
            ),
        ),
        (
            "TH-F-012 Monica Pinzon.pdf",
            "pdf",
            th_f_012(
                "Mónica Pinzón Ariza",
                "1.014.556.789",
                "Auxiliar de operaciones",
                "Operaciones",
                "Barranquilla",
                "2026-11-30",
                "2026-12-02",
                "Capacitación sistema de turnos",
                "$1.150.000",
                "Ing. Carlos Méndez",
                False,
            ),
        ),
    ],
    expected=[
        E(
            "TH-F-012 Andres Cuervo.pdf",
            TRV,
            "HUMAN_RESOURCES",
            FILE,
            "TH-F-012 firmado por el jefe; con anticipación suficiente (viaje 30 nov)",
        ),
        E(
            "TH-F-012 Monica Pinzon.pdf",
            TRV,
            "SENDER",
            RET,
            "TH-F-012 sin firma del jefe: devolver al remitente",
        ),
    ],
)

case(
    D(5, 9, 50),
    "Óscar Bermúdez <oscar.bermudez@terminalesandinas.example>",
    "Anticipo gastos de viaje Cali",
    "Martha, envío la solicitud de anticipo para el viaje a Cali, ya firmada por mi jefa.\nÓscar",
    [
        (
            "Solicitud anticipo Oscar Bermudez.pdf",
            "pdf",
            [
                "TERMINALES ANDINAS DE CARGA S.A.",
                "SOLICITUD DE ANTICIPO PARA GASTOS (formato libre)",
                "",
                "Solicitante: Óscar Bermúdez Castro - C.C. 79.880.112",
                "Cargo: Profesional jurídico",
                "Destino: Cali, audiencia de conciliación",
                "Fechas: 2026-11-26 al 2026-11-27",
                "Valor: $890.000",
                "",
                "Aprobó: Dra. Liliana Ospina - Jefe Oficina Jurídica",
                "Firma: ~~ Ospina ~~ (firmado)",
            ],
        )
    ],
    expected=[
        E(
            "Solicitud anticipo Oscar Bermudez.pdf",
            TRV,
            "SENDER",
            RET,
            "Aunque está firmada por la jefa, no viene en el formato TH-F-012: devolver para que use el formato",
        )
    ],
)

# ============================== PETICIONES ===============================
case(
    D(3, 10, 5),
    "Manuel Ricardo Castaño <mrcastano@correoficticio.example>",
    "Derecho de petición - información procesos de selección",
    "Señores\nTerminales Andinas de Carga S.A.\n\nRespetados señores:\n\nEn ejercicio del derecho "
    "fundamental de petición consagrado en el artículo 23 de la Constitución, solicito se me informe "
    "qué procesos de selección de personal operativo tiene abiertos la empresa, cuáles son los requisitos "
    "y por qué medio se reciben hojas de vida.\n\nRecibo respuesta en este correo.\n\nManuel Ricardo "
    "Castaño\nC.C. 1.023.889.456",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "Derecho de petición de información general: 15 días hábiles desde el 4 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(5, 14, 20),
    "Gloria Inés Cárdenas <gloriaines.cardenas@correoficticio.example>",
    "Solicitud de copias",
    "Buenas tardes,\n\nTrabajé en la empresa como auxiliar de bodega entre 2021 y 2024. Solicito "
    "respetuosamente copia de mi contrato de trabajo y copia de los desprendibles de nómina del año 2024.\n\n"
    "Gracias,\nGloria Inés Cárdenas\nC.C. 39.554.221",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "Petición que solo pide copias de documentos: 10 días hábiles desde el 6 nov",
            vence=("bd", 10),
        )
    ],
)

case(
    D(9, 9, 0),
    "Jurídica Logística Andes Cargo <juridica@andescargo.example>",
    "Consulta tarifa almacenamiento contenedores en tránsito",
    "Señores TAC:\n\nAndes Cargo S.A.S., cliente del terminal, respetuosamente solicita a ustedes emitir "
    "su concepto sobre si la tarifa de almacenamiento publicada para 2026 aplica a los contenedores en "
    "tránsito aduanero (DTA) que permanecen menos de 48 horas en el patio, y cuál es el fundamento "
    "contractual de dicha interpretación.\n\nNo se trata de una queja; requerimos el concepto para "
    "planear la operación de 2027.\n\nCordialmente,\nDiana Marcela Ruiz\nAbogada - Andes Cargo S.A.S.",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "Consulta en la que se pide un concepto: 30 días hábiles desde el 10 nov (8 dic y 25 dic festivos)",
            vence=("bd", 30),
        )
    ],
)

case(
    D(10, 16, 45),
    "Luz Marina Patiño <luzmarina.patino@correoficticio.example>",
    "Peticion",
    "Señores Terminales Andinas\n\nSolicito copia del acta del comité de convivencia laboral del 15 de "
    "septiembre de 2026 y les pido que me informen en qué estado está la queja por acoso que radiqué en "
    "agosto y qué medidas se han tomado.\n\nLuz Marina Patiño\nC.C. 52.110.987",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "Pide copias y además información: 15 días hábiles (regla de la abogada) desde el 11 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(15, 20, 30),
    "Edwin Rodriguez <edwinrodri1985@correoficticio.example>",
    "liquidacion",
    "buenas noches, yo sali de la empresa el 30 de septiembre y todavia no me han consignado la "
    "liquidacion, les pido que me informen cuando me la pagan y cuanto es el valor porque nadie me "
    "contesta en el telefono\n\nedwin rodriguez\ncc 80.990.123",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            'Petición implícita ("les pido que me informen") de ex trabajador, no es usuario del terminal: '
            "15 días hábiles; recibido domingo 15 nov, se cuenta desde el 17 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(12, 11, 30),
    "Ramiro Ernesto Vargas <ramiro.vargas.abogado@correoficticio.example>",
    "Derecho de petición aportes pensionales - Ramiro Vargas",
    "Señores Terminales Andinas de Carga S.A.\n\nObrando en nombre propio, solicito se me certifique y "
    "explique por qué no aparecen en mi historia laboral de Colpensiones los aportes de los meses de "
    "marzo a junio de 2023, periodo en que laboré para ustedes, y qué gestiones harán para corregirlo.\n\n"
    "Advierto que, de no recibir respuesta de fondo dentro del término legal, interpondré acción de "
    "tutela para la protección de mis derechos fundamentales.\n\nRamiro Ernesto Vargas\nC.C. 79.123.004",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "URGENTE: el peticionario anuncia acción de tutela. Petición general: 15 días hábiles desde el 13 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(13, 8, 10),
    "Rosalba Méndez <rosalba.mendez.vecina@correoficticio.example>",
    "Tractomulas parqueadas en la calle 13 - vecinos barrio La Esperanza",
    "Buenos días.\n\nSoy vecina del barrio La Esperanza, al lado del terminal. Desde hace un mes las "
    "tractomulas que esperan turno para entrar se parquean sobre la calle 13 toda la noche, con el motor "
    "prendido, y no dejan dormir ni salir los carros. Estoy cansada de esta situación.\n\nSolicito que "
    "tomen medidas para que los camiones esperen dentro del terminal y que me informen qué van a hacer.\n\n"
    "Rosalba Méndez\nCra 4 No. 13-22",
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            "Aunque es una queja, la vecina no es usuaria del terminal (no es transportadora ni cliente): "
            "se trata como petición, 15 días hábiles desde el 17 nov (16 festivo)",
            vence=("bd", 15),
        )
    ],
)

case(
    D(17, 12, 2),
    "Carolina Arias <carolina.arias@terminalesandinas.example>",
    "RV: Derecho de petición accidente contratista",
    "Martha, esta señora me escribió esta mañana a mi correo, te lo reenvío para que lo radiques.\n"
    "Carolina - Seguridad y salud en el trabajo\n\n"
    "-----Mensaje original-----\nDe: Rosa Elvira Gómez <rosaelvira.gomez@correoficticio.example>\n"
    "Enviado: martes, 17 de noviembre de 2026 8:41 a. m.\nPara: Carolina Arias\n"
    "Asunto: Derecho de petición\n\nAdjunto derecho de petición. Gracias.",
    [
        (
            "Derecho de peticion - Rosa Elvira Gomez.docx",
            "docx",
            [
                "DERECHO DE PETICIÓN",
                "Funza, 16 de noviembre de 2026",
                "",
                "Señores TERMINALES ANDINAS DE CARGA S.A.",
                "",
                "Yo, Rosa Elvira Gómez, identificada con C.C. 20.334.876, esposa del señor Luis Alberto Peña, "
                "trabajador del contratista que sufrió un accidente en el patio 2 el 28 de octubre, solicito:",
                "1. Que me informen qué aseguradora de riesgos laborales cubre a mi esposo.",
                "2. Que me expliquen qué medidas tomó la empresa después del accidente.",
                "3. Que me indiquen a quién debo dirigirme para los gastos médicos.",
                "",
                "Recibo notificaciones en rosaelvira.gomez@correoficticio.example",
                "",
                "Rosa Elvira Gómez",
            ],
        )
    ],
    expected=[
        E(
            "Derecho de peticion - Rosa Elvira Gomez.docx",
            PET,
            "LEGAL",
            FILE,
            "Derecho de petición reenviado internamente (llegó el mismo 17 nov): 15 días hábiles desde el 18 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(6, 10, 0),
    "Asovendedores Funza <asovendedoresfunza@correoficticio.example>",
    "solicitud",
    "Buenos dias adjuntamos carta escaneada. Atentamente la junta directiva.",
    [
        (
            "carta asociacion.pdf",
            "scan",
            [
                "ASOCIACION DE VENDEDORES INFORMALES DE FUNZA",
                "Funza, 5 de noviembre de 2026",
                "",
                "Señores",
                "TERMINALES ANDINAS DE CARGA S.A.",
                "",
                "Respetados señores:",
                "Por medio de la presente solicitamos copia de las actas de las reuniones",
                "realizadas entre la empresa y nuestra asociacion los dias 12 de agosto",
                "y 9 de septiembre de 2026, y copia del listado de asistencia de dichas",
                "reuniones.",
                "",
                "Agradecemos su atencion.",
                "",
                "Blanca Nelly Ospina",
                "Presidenta",
            ],
        )
    ],
    expected=[
        E(
            "carta asociacion.pdf",
            PET,
            "LEGAL",
            FILE,
            "Petición (escaneada) que solo pide copias de actas y listados: 10 días hábiles desde el 9 nov",
            vence=("bd", 10),
        )
    ],
)

html = (
    "<html><body><p>Cordial saludo,</p><p>Soy estudiante de la Especialización en Logística de la "
    "Universidad Ficticia de la Sabana y estoy haciendo mi trabajo de grado sobre terminales "
    "interiores de carga.</p><p>Les pido que me informen, si es posible:</p><ol>"
    "<li>El número de contenedores movilizados en 2025.</li><li>El tiempo promedio de estadía de un "
    "vehículo en el terminal.</li></ol><p>Muchas gracias por su colaboración.</p>"
    "<p>Juliana Torres Quiroga<br>C.C. 1.026.334.778</p></body></html>"
)
case(
    D(11, 10, 25),
    "Juliana Torres <juliana.torres@unificticia.example>",
    "Solicitud de información para trabajo de grado",
    "Cordial saludo,\nSoy estudiante... Les pido que me informen el número de contenedores movilizados en "
    "2025 y el tiempo promedio de estadía de un vehículo.\nJuliana Torres Quiroga",
    html=html,
    expected=[
        E(
            "EMAIL_BODY",
            PET,
            "LEGAL",
            FILE,
            'Solicitud de información ("les pido que me informen"), no es queja: petición, '
            "15 días hábiles desde el 12 nov",
            vence=("bd", 15),
        )
    ],
)

# ============================== OFICIOS / ENTES ==========================
case(
    D(4, 11, 0),
    "Ventanilla Única Contraloría Departamental <notificaciones@contraloriacund-ficticia.example>",
    "Requerimiento de información AF-2026-118",
    "Se remite oficio de requerimiento. Por favor no responder a este buzón.",
    [
        (
            "Oficio AF-2026-118.pdf",
            "pdf",
            oficio(
                "CONTRALORÍA DEPARTAMENTAL (ENTIDAD FICTICIA)",
                "AF-2026-118",
                "Bogotá, 3 de noviembre de 2026",
                "Requerimiento de información - auditoría financiera vigencia 2025",
                [
                    "En desarrollo de la auditoría financiera a la vigencia 2025, se solicita remitir la",
                    "relación de contratos suscritos con recursos de la concesión, con sus respectivos",
                    "soportes de pago, dentro de los diez (10) días hábiles siguientes al recibo",
                    "de la presente comunicación.",
                ],
                "Mauricio Pedraza Leal - Auditor fiscal",
            ),
        )
    ],
    expected=[
        E(
            "Oficio AF-2026-118.pdf",
            OVS,
            "LEGAL",
            FILE,
            "URGENTE - Contraloría: plazo del oficio diez (10) días hábiles, contados desde el 5 nov",
            vence=("bd", 10),
        )
    ],
)

case(
    D(10, 15, 30),
    "Procuraduría Provincial <ventanilla@procuraduria-ficticia.example>",
    "OFICIO PPF-3321-2026",
    "Remitimos oficio escaneado para su conocimiento y fines pertinentes.",
    [
        (
            "PPF-3321-2026.pdf",
            "scan",
            oficio(
                "PROCURADURIA PROVINCIAL DE FUNZA (FICTICIA)",
                "PPF-3321-2026",
                "Funza, 9 de noviembre de 2026",
                "Solicitud de informacion - queja ciudadana",
                [
                    "Con ocasion de la queja presentada por la comunidad del sector",
                    "La Esperanza, este despacho solicita informar las medidas adoptadas",
                    "frente al estacionamiento de vehiculos de carga en la via publica.",
                    "La respuesta debera allegarse dentro de los cinco (5) dias habiles",
                    "siguientes al recibo de este oficio.",
                ],
                "Procurador Provincial",
            ),
        )
    ],
    expected=[
        E(
            "PPF-3321-2026.pdf",
            OVS,
            "LEGAL",
            FILE,
            "URGENTE - Procuraduría (oficio escaneado): cinco (5) días hábiles desde el 11 nov",
            vence=("bd", 5),
        )
    ],
)

case(
    D(5, 16, 0),
    "Personería Municipal de Funza <personeria@personeriafunza-ficticia.example>",
    "Oficio PM-0457 - solicitud de información",
    "Buenas tardes, se adjunta oficio PM-0457 de la Personería Municipal.",
    [
        (
            "PM-0457.pdf",
            "pdf",
            oficio(
                "PERSONERÍA MUNICIPAL DE FUNZA (ENTIDAD FICTICIA)",
                "PM-0457",
                "Funza, 5 de noviembre de 2026",
                "Solicitud de información - trabajadores de contratistas",
                [
                    "En ejercicio de las funciones de guarda de los derechos humanos, este despacho",
                    "solicita informar el número de trabajadores de empresas contratistas que laboran",
                    "en el terminal y la afiliación a seguridad social de los mismos.",
                    "Plazo para responder: ocho (8) días calendario contados a partir del recibo",
                    "del presente oficio.",
                ],
                "Personero Municipal",
            ),
        )
    ],
    expected=[
        E(
            "PM-0457.pdf",
            OVS,
            "LEGAL",
            FILE,
            "URGENTE - Personería: el oficio da ocho (8) días CALENDARIO desde el recibo (5 nov) → 13 nov",
            vence=("cal", 8),
        )
    ],
)

case(
    D(17, 10, 15),
    "Juzgado Primero Civil Municipal de Funza <j01cmfunza@ramajudicial-ficticia.example>",
    "NOTIFICACIÓN AUTO ADMISORIO ACCIÓN DE TUTELA 2026-00318",
    "Se notifica auto admisorio de tutela. Cualquier respuesta debe enviarse al correo del despacho.",
    [
        (
            "Auto admisorio 2026-00318.pdf",
            "pdf",
            [
                "JUZGADO PRIMERO CIVIL MUNICIPAL DE FUNZA (FICTICIO)",
                "",
                "Acción de tutela No. 2026-00318",
                "Accionante: Ramiro Ernesto Vargas",
                "Accionada: Terminales Andinas de Carga S.A.",
                "",
                "AUTO ADMISORIO - Funza, 13 de noviembre de 2026",
                "",
                "PRIMERO: ADMITIR la acción de tutela de la referencia.",
                "SEGUNDO: NOTIFICAR a la accionada para que, en el término de dos (2) días",
                "contados a partir de la notificación, ejerza su derecho de defensa y rinda",
                "informe sobre los hechos de la solicitud.",
                "",
                "NOTIFÍQUESE Y CÚMPLASE",
                "",
                "Juez",
            ],
        )
    ],
    expected=[
        E(
            "Auto admisorio 2026-00318.pdf",
            OVS,
            "LEGAL",
            FILE,
            "URGENTE - Juzgado, tutela: dos (2) días (términos judiciales en días hábiles) desde el 18 nov",
            vence=("bd", 2),
        )
    ],
)

case(
    D(13, 15, 0),
    "Juzgado Segundo Civil del Circuito <j02cctofunza@ramajudicial-ficticia.example>",
    "Oficio 1877 - medida cautelar embargo de créditos",
    "Se remite oficio para su cumplimiento.",
    [
        (
            "Oficio 1877.pdf",
            "pdf",
            [
                "JUZGADO SEGUNDO CIVIL DEL CIRCUITO DE FUNZA (FICTICIO)",
                "",
                "Oficio No. 1877",
                "Funza, 12 de noviembre de 2026",
                "",
                "Señores TERMINALES ANDINAS DE CARGA S.A.",
                "",
                "Proceso ejecutivo 2026-00412 de Banco Ficticio S.A. contra Montajes Rápidos S.A.S.",
                "",
                "Comunico que se decretó el EMBARGO de los créditos que la demandada tenga a su favor en esa",
                "empresa. Sírvase informar a este despacho, dentro de los tres (3) días hábiles siguientes",
                "al recibo, si existen sumas pendientes de pago a la demandada.",
                "",
                "Secretario",
            ],
        )
    ],
    expected=[
        E(
            "Oficio 1877.pdf",
            OVS,
            "LEGAL",
            FILE,
            "URGENTE - Juzgado: tres (3) días hábiles desde el 17 nov (16 nov festivo)",
            vence=("bd", 3),
        )
    ],
)

# ============================== QUEJAS ===================================
case(
    D(3, 13, 40),
    "Coomultracarga <gerencia@coomultracarga.example>",
    "Queja por cobros de báscula duplicados",
    "Señores Atención al Usuario TAC:\n\nLa Cooperativa Multiactiva de Transportadores de Carga presenta "
    "queja porque a varios de nuestros asociados les están cobrando dos veces el pesaje en báscula cuando "
    "el vehículo reingresa el mismo día. Adjuntamos relación de placas en el cuerpo: TKL-221, SXP-908, "
    "WMN-334.\n\nEsperamos solución.\n\nGerencia - Coomultracarga",
    expected=[
        E(
            "EMAIL_BODY",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Queja de cooperativa de transportadores (usuarios del terminal): 15 días hábiles desde el 4 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(9, 6, 50),
    "Albeiro Gutiérrez <albeiro.gutierrez.conductor@correoficticio.example>",
    "Reclamo - me retuvieron el manifiesto",
    "Buenos días. El sábado entré con la tractomula placa SNK-772 a descargar y en la portería me "
    "retuvieron el manifiesto de carga y no me lo devolvieron, tuve que salir sin él y la empresa "
    "transportadora me va a multar. Es un mal servicio. Les pido que me informen dónde puedo recoger el "
    "documento y quién responde por la multa.\n\nAlbeiro Gutiérrez - conductor",
    expected=[
        E(
            "EMAIL_BODY",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Queja de un conductor usuario del terminal; aunque pide información sigue siendo queja de "
            "usuario (no petición): 15 días hábiles desde el 10 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(11, 9, 15),
    "Comercio Exterior Importadora Nogal <comex@importadoranogal.example>",
    "Reclamo contenedor MSKU 448812-0 averiado",
    "Señores,\nAdjuntamos reclamo formal por la avería de nuestro contenedor durante su permanencia en "
    "el patio 3.\nImportadora Nogal S.A.S.",
    [
        (
            "Reclamo contenedor MSKU4488120.docx",
            "docx",
            [
                "RECLAMO FORMAL",
                "Bogotá, 10 de noviembre de 2026",
                "",
                "Importadora Nogal S.A.S., cliente del terminal, presenta reclamo por los siguientes hechos:",
                "1. El contenedor MSKU 448812-0 ingresó al patio 3 el 2 de noviembre en perfecto estado.",
                "2. Al retirarlo el 9 de noviembre presentaba una abolladura en la puerta y el sello roto.",
                "3. La mercancía (electrodomésticos) presenta faltantes por $14.500.000.",
                "Solicitamos que se responda por los daños y faltantes.",
                "",
                "Hernán Ocampo",
                "Jefe de comercio exterior",
            ],
        )
    ],
    expected=[
        E(
            "Reclamo contenedor MSKU4488120.docx",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Reclamo de un cliente del terminal: 15 días hábiles desde el 12 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(8, 23, 10),
    "transportes el ruiseñor <transporteselruisenor@correoficticio.example>",
    "QUEJA PESIMO SERVICIO PORTERIA",
    "SEÑORES TERMINAL ANDINAS. NUEVAMENTE NUESTROS CONDUCTORES ESPERARON MAS DE 6 HORAS EN LA FILA DE "
    "LA PORTERIA 2 EL VIERNES 6 DE NOVIEMBRE Y NO HABIA NI UN FUNCIONARIO DANDO INFORMACION. ESTO YA ES "
    "COSTUMBRE. EXIGIMOS UNA RESPUESTA SERIA.\n\nTRANSPORTES EL RUISEÑOR LTDA",
    expected=[
        E(
            "EMAIL_BODY",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Queja de empresa transportadora (en mayúsculas, sin tildes); recibido domingo 8 nov: "
            "15 días hábiles desde el 9 nov",
            vence=("bd", 15),
        )
    ],
)

html = (
    "<html><body><p>Buenos días,</p><p>Como empresa transportadora que opera diariamente en el "
    "terminal queremos dejar constancia de <b>malos tratos</b> por parte del vigilante del turno de la "
    "mañana en la portería 1 hacia nuestro conductor Jairo Benítez el 12 de noviembre.</p><p>"
    "Pedimos que se investigue y se tomen correctivos.</p><p>Atentamente,<br>Logística Integral "
    "del Centro S.A.S.</p></body></html>"
)
case(
    D(13, 11, 20),
    "Logística Integral del Centro <operaciones@logintcentro.example>",
    "Queja contra personal de portería",
    "",
    html=html,
    html_only=True,
    expected=[
        E(
            "EMAIL_BODY",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Queja de transportadora usuaria del terminal (cuerpo HTML): 15 días hábiles desde el 17 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(17, 9, 35),
    "Jefatura de Patio <jefe.patio@terminalesandinas.example>",
    "FW: reclamo cobro parqueadero no autorizado",
    "Martha, este reclamo me llegó a mí, te lo paso para radicar y que lo maneje Atención al usuario.\n\n"
    "---------- Forwarded message ---------\nDe: Transportes Unidos del Sur <tesoreria@transunidossur.example>\n"
    "Date: mar, 17 nov 2026 a las 7:58\nSubject: reclamo cobro parqueadero no autorizado\n\n"
    "Señores TAC: en la cuenta de servicios de octubre nos cobraron 14 noches de parqueadero de vehículos "
    "que no pernoctaron en el terminal. Solicitamos la revisión y la anulación de ese cobro.\n"
    "Tesorería - Transportes Unidos del Sur",
    expected=[
        E(
            "EMAIL_BODY",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Reclamo de transportadora (cliente del terminal) reenviado por el jefe de patio el mismo día: "
            "15 días hábiles desde el 18 nov",
            vence=("bd", 15),
        )
    ],
)

case(
    D(5, 10, 45),
    "Pedro Nel Rincón <pedronel.rincon@correoficticio.example>",
    "carta",
    "adjunto carta, gracias",
    [
        (
            "IMG_20261104_carta.pdf",
            "scan",
            [
                "Funza 4 de noviembre 2026",
                "",
                "Señores terminal andinas de carga",
                "",
                "Yo Pedro Nel Rincon conductor de la empresa Carga Pesada del Llano",
                "quiero poner una queja porque los baños de la zona de conductores",
                "llevan 3 semanas sin agua y sin aseo, es una falta de respeto con",
                "nosotros que esperamos hasta 10 horas para cargar.",
                "",
                "Espero que arreglen eso.",
                "",
                "Pedro Nel Rincon",
                "cc 17.445.889",
            ],
        )
    ],
    expected=[
        E(
            "IMG_20261104_carta.pdf",
            CMP,
            "CUSTOMER_SERVICE",
            FILE,
            "Queja manuscrita/escaneada de conductor usuario del terminal: 15 días hábiles desde el 6 nov",
            vence=("bd", 15),
        )
    ],
)

# ============================== COTIZACIONES =============================
s = SUP["llano"]
case(
    D(4, 15, 0),
    f"Ventas Suministros del Llano <{s['mail']}>",
    "Cotizacion COT-2026-0893 overoles",
    "Buenas tardes, adjuntamos cotización de overoles ignífugos según lo solicitado por Compras.",
    [
        (
            "COT-2026-0893.pdf",
            "pdf",
            [
                s["name"],
                f"NIT {s['nit']}",
                "",
                "COTIZACIÓN No. COT-2026-0893",
                "Fecha: 2026-11-04",
                "Cliente: " + TAC,
                "",
                "Overol ignífugo talla M-XL (40 und)   $6.800.000",
                "Validez de la oferta: 30 días",
                "Tiempo de entrega: 10 días hábiles",
            ],
        )
    ],
    expected=[E("COT-2026-0893.pdf", QUO, "PROCUREMENT", FILE, "Cotización: va a Compras")],
)

html = (
    "<html><body><h2>Llantas del Norte</h2><p>Señores Terminales Andinas,</p><p>Atendiendo la "
    "solicitud telefónica de su jefe de mantenimiento, presentamos oferta:</p><table border='1'>"
    "<tr><th>Referencia</th><th>Cant</th><th>Valor unitario</th></tr>"
    "<tr><td>Llanta 295/80R22.5 direccional</td><td>12</td><td>$1.420.000</td></tr>"
    "<tr><td>Llanta 11R22.5 tracción</td><td>8</td><td>$1.360.000</td></tr></table>"
    "<p>Precios antes de IVA. Validez 15 días.</p><p>Asesor comercial: Felipe Cuéllar</p></body></html>"
)
case(
    D(9, 12, 0),
    "Llantas del Norte <ventas@llantasdelnorte.example>",
    "Propuesta llantas para tractocamiones",
    "Ver oferta en HTML.",
    html=html,
    expected=[
        E(
            "EMAIL_BODY",
            QUO,
            "PROCUREMENT",
            FILE,
            "Oferta de precios en el cuerpo del correo de un proveedor no registrado: cotización a Compras",
        )
    ],
)

s = SUP["monta"]
case(
    D(12, 8, 30),
    f"Facturas Montacargas El Puerto <{s['mail']}>",
    "Factura MP-5531 y cotización cambio de mástil",
    "Buenos días, adjuntamos la factura MP-5531 de la visita correctiva (OC-2026-0420) y, como lo pidió "
    "el jefe de mantenimiento, la cotización COT-MP-112 para el cambio del mástil del montacargas 2.\n"
    "Cordialmente,\nMantenimiento de Montacargas El Puerto",
    [
        (
            "MP-5531.pdf",
            "pdf",
            invoice(
                s,
                "MP-5531",
                "2026-11-11",
                [("Visita correctiva montacargas 2", 980000)],
                oc="OC-2026-0420",
            ),
        ),
        (
            "COT-MP-112.pdf",
            "pdf",
            [
                s["name"],
                f"NIT {s['nit']}",
                "",
                "COTIZACIÓN COT-MP-112",
                "Fecha: 2026-11-11",
                "Cambio de mástil montacargas 2 (repuesto + mano de obra)   $18.400.000",
                "Validez: 20 días",
            ],
        ),
    ],
    expected=[
        E(
            "MP-5531.pdf",
            INV,
            "ACCOUNTS_PAYABLE",
            FILE,
            "Factura de proveedor registrado con OC-2026-0420",
        ),
        E(
            "COT-MP-112.pdf",
            QUO,
            "PROCUREMENT",
            FILE,
            "Cotización adjunta en el mismo correo: a Compras",
        ),
    ],
)

case(
    D(6, 17, 45),
    "Bioplagas Control Integral <comercial@bioplagas.example>",
    "Propuesta economica fumigacion bodegas",
    "Buenas tardes,\nenviamos la propuesta economica para el control de roedores y fumigacion de las "
    "bodegas 1 a 4 que nos solicitaron en la visita técnica.\nQuedamos atentos.\nBioplagas",
    [
        (
            "Propuesta economica Bioplagas TAC.docx",
            "docx",
            [
                "PROPUESTA ECONÓMICA",
                "Bioplagas Control Integral S.A.S. - NIT 901.442.110-5",
                "",
                "Cliente: Terminales Andinas de Carga S.A.",
                "Servicio: control integral de plagas bodegas 1 a 4",
                "Frecuencia: mensual durante 12 meses",
                "Valor mensual: $2.150.000 + IVA",
                "Validez de la propuesta: 30 días",
                "",
                "Cordialmente,",
                "Área comercial",
            ],
        )
    ],
    expected=[
        E(
            "Propuesta economica Bioplagas TAC.docx",
            QUO,
            "PROCUREMENT",
            FILE,
            "Propuesta económica = cotización: a Compras (proveedor no registrado no cambia la ruta)",
        )
    ],
)

# ============================== PUBLICIDAD ===============================
html = (
    "<html><body style='font-family:Arial'><h1>¡30% de descuento en tu renovación!</h1><p>Hola, "
    "cliente de Software Contable Nube:</p><p>Renueva tu licencia anual antes del 30 de noviembre y "
    "obtén 30% de descuento + migración gratuita a la nube.</p><p><a href='https://contablenube.example/promo'>"
    "Aprovechar oferta</a></p><p style='font-size:10px'>Para no recibir más correos haz clic aquí.</p>"
    "</body></html>"
)
case(
    D(7, 6, 0),
    "Software Contable Nube <promociones@contablenube.example>",
    "🎁 Renueva con 30% OFF - solo este mes",
    "",
    html=html,
    html_only=True,
    expected=[
        E(
            "EMAIL_BODY",
            ADV,
            "NONE",
            NOF,
            "Correo promocional de un proveedor registrado: publicidad, no se radica",
        )
    ],
)

html = (
    "<html><body><h2>LLANTATON 2026</h2><p>Precios increíbles en llantas para tractomula, "
    "volqueta y montacargas. Financiación hasta 12 meses.</p><p>Visítanos o escríbenos por WhatsApp.</p>"
    "</body></html>"
)
case(
    D(10, 7, 0),
    "Llantas Express Colombia <marketing@llantasexpress.example>",
    "LLANTATON: hasta 40% en llantas de carga",
    "",
    html=html,
    html_only=True,
    expected=[E("EMAIL_BODY", ADV, "NONE", NOF, "Publicidad masiva, no se radica")],
)

case(
    D(16, 8, 0),
    "Expo Logística Andina <eventos@expologisticaandina.example>",
    "Invitación: Expo Logística Andina 2027 - inscripción anticipada",
    "Estimado profesional de la logística:\n\nLo invitamos a la Expo Logística Andina 2027, del 10 al 12 "
    "de marzo en Corferias (ficticio). Inscríbase antes del 15 de diciembre y obtenga 20% de descuento en "
    "su stand.\n\nPara darse de baja responda REMOVER.",
    expected=[
        E("EMAIL_BODY", ADV, "NONE", NOF, "Invitación comercial a feria: publicidad, no se radica")
    ],
)

case(
    D(11, 5, 30),
    "FacturaYa <hola@facturaya.example>",
    "Su FACTURA electrónica sigue en papel? Le ayudamos",
    "Buenos días,\n\n¿Todavía recibe facturas y cuentas de cobro en PDF y las digita a mano? Con FacturaYa "
    "las facturas de sus proveedores entran solas a su ERP. Agende una demo gratuita esta semana.\n\n"
    "Equipo comercial FacturaYa\nSi no desea recibir más mensajes, responda NO.",
    expected=[
        E(
            "EMAIL_BODY",
            ADV,
            "NONE",
            NOF,
            "Publicidad de software (menciona 'factura' pero no es una factura): no se radica",
        )
    ],
)

case(
    D(14, 9, 15),
    "Capacitaciones Jurídicas Express <cursos@capjuridicas.example>",
    "Curso virtual: cómo responder derechos de petición y tutelas a tiempo",
    "Señores Oficina Jurídica:\n\n¿Se le vencen los derechos de petición? Inscríbase en nuestro curso "
    "virtual de 16 horas sobre términos de respuesta, derechos de petición y acción de tutela. Inicio: "
    "1 de diciembre. Valor: $390.000 por persona; 2x1 para inscripciones antes del 25 de noviembre.\n\n"
    "Capacitaciones Jurídicas Express",
    expected=[
        E(
            "EMAIL_BODY",
            ADV,
            "NONE",
            NOF,
            "Publicidad de un curso (menciona 'derecho de petición' y 'tutela' pero no lo es): no se radica",
        )
    ],
)


# --------------------------------------------------------------------------
# Construcción
# --------------------------------------------------------------------------


def build():
    for f in EMAILS.glob("b*.eml"):
        f.unlink()
    CASES.sort(key=lambda c: c["dt"])
    assert len(CASES) == 60, len(CASES)
    rows = []
    for i, c in enumerate(CASES, 1):
        name = f"b{i:02d}.eml"
        m = EmailMessage()
        m["From"] = c["frm"]
        m["To"] = c["to"]
        m["Date"] = format_datetime(c["dt"])
        m["Subject"] = c["subject"]
        dom = c["frm"].split("@")[-1].rstrip(">")
        m["Message-ID"] = make_msgid(domain=dom)
        if c["html_only"]:
            m.set_content(c["html"], subtype="html")
        else:
            m.set_content(c["body"])
            if c["html"]:
                m.add_alternative(c["html"], subtype="html")
        for fname, kind, lines in c["atts"]:
            data, mt, st = render(kind, lines)
            m.add_attachment(data, maintype=mt, subtype=st, filename=fname)
        (EMAILS / name).write_bytes(bytes(m))
        recv = c["dt"].date()
        for e in c["expected"]:
            v = e["vence"]
            if v is None:
                vs = ""
            elif v[0] == "bd":
                vs = add_business(recv, v[1]).isoformat()
            else:
                vs = add_calendar(recv, v[1]).isoformat()
            rows.append(
                dict(
                    correo=name,
                    documento=e["documento"],
                    tipo=e["tipo"],
                    dependencia=e["dependencia"],
                    accion=e["accion"],
                    vence=vs,
                    radicado="",
                    observacion=e["observacion"],
                )
            )
    with open(OUT / "esperado-ciego.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "correo",
                "documento",
                "tipo",
                "dependencia",
                "accion",
                "vence",
                "radicado",
                "observacion",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    rows = build()
    from collections import Counter

    print(len(rows), "documentos")
    print(Counter(r["tipo"] for r in rows))
    print(Counter((r["dependencia"], r["accion"]) for r in rows))
