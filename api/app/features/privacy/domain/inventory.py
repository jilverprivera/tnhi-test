"""Personal data inventory (Ley 1581 de 2012, Decreto 1377 de 2013): what Docket holds and why."""

from pydantic import BaseModel


class PersonalDataItem(BaseModel):
    data: str
    subjects: str  # titulares
    stored_in: str
    purpose: str
    legal_basis: str
    access: str
    retention: str


INVENTORY: list[PersonalDataItem] = [
    PersonalDataItem(
        data="Nombre, cédula y correo del remitente",
        subjects="Ciudadanos, empleados, transportadores, contactos de proveedores",
        stored_in="Bandeja (propuesta) y libro de radicación (remitente / identificación)",
        purpose="Radicar, responder y hacer trazable la correspondencia recibida",
        legal_basis="Obligación legal de radicar y responder (Ley 1755 de 2015; Ley 594 de 2000)",
        access="Radicación y Coordinación; dependencias que reciben el reenvío",
        retention="Según la TRD del tipo documental",
    ),
    PersonalDataItem(
        data="Contenido de peticiones y quejas (puede incluir datos sensibles)",
        subjects="Ciudadanos y usuarios del terminal",
        stored_in="Archivo original y texto extraído en la bandeja",
        purpose="Tramitar la petición o queja dentro del plazo legal",
        legal_basis="Obligación legal (Ley 1755 de 2015)",
        access="Radicación, Coordinación y Jurídica / Atención al usuario",
        retention="Según la TRD; al eliminarse se borra el contenido y queda solo el índice",
    ),
    PersonalDataItem(
        data="Datos de viáticos (cédula, cargo, destino, valores)",
        subjects="Empleados de TAC",
        stored_in="Archivo original, texto extraído y libro",
        purpose="Trámite y soporte contable del anticipo",
        legal_basis="Relación laboral y obligación contable",
        access="Radicación, Coordinación y Talento humano",
        retention="10 años (soporte contable)",
    ),
    PersonalDataItem(
        data="Cuenta bancaria y NIT de proveedores (personas naturales incluidas)",
        subjects="Proveedores",
        stored_in="Maestro de proveedores (ERP) y facturas en la bandeja",
        purpose="Pago y prevención de fraude por cambio de cuenta",
        legal_basis="Relación contractual y obligación contable",
        access="Radicación, Coordinación y Cuentas por pagar",
        retention="10 años (soporte contable)",
    ),
]

# What never leaves TAC with personal data in it
SAFEGUARDS = [
    "OCR y reglas locales: ningún documento se envía a terceros.",
    "IA opcional apagada; si se aprueba, recibe el texto enmascarado y solo bajo contrato.",
    "Auditoría y métricas sin datos personales (identificadores enmascarados, solo conteos).",
    "Consultas de titulares por cuerpo de la solicitud, nunca en la URL ni en los logs.",
    "Al eliminar por TRD se borra el contenido y el archivo; queda el índice exigido por la Ley 594.",
]
