from __future__ import annotations

from typing import Literal, TypedDict

InvoiceDocumentType = Literal["invoice"]
InvoiceTemplate = Literal["ledger"]
QrMode = Literal["", "contact", "epc", "paymentLink"]
StampStyle = Literal["round", "square", "none"]
LogoMimeType = Literal["image/png", "image/jpeg"]
VatCategoryCode = Literal["AE", "B", "E", "G", "K", "L", "M", "O", "S", "Z"]
TaxIdRole = Literal["seller-id", "legal-registration", "tax-registration", "vat"]


class PublicPartyV1(TypedDict):
    name: str
    addressLines: list[str]


class _PublicItemRequired(TypedDict):
    description: str
    quantity: float
    unitPrice: float
    taxRate: float


class PublicItemV1(_PublicItemRequired, total=False):
    taxLabel: str


class PublicPaymentV1(TypedDict, total=False):
    bankName: str
    iban: str
    bic: str
    accountNumber: str
    routingNumber: str
    reference: str
    poNumber: str
    terms: str
    dueText: str
    qrMode: QrMode


class PublicLogoV1(TypedDict):
    data: str
    mimeType: LogoMimeType


class PublicBrandingV1(TypedDict, total=False):
    accentColor: str
    stampStyle: StampStyle
    logo: PublicLogoV1


class _PublicDocumentRequired(TypedDict):
    type: InvoiceDocumentType
    issueDate: str
    currency: str
    seller: PublicPartyV1
    buyer: PublicPartyV1
    items: list[PublicItemV1]


class PublicDocumentV1(_PublicDocumentRequired, total=False):
    number: str
    dueDate: str
    locale: str
    template: InvoiceTemplate
    payment: PublicPaymentV1
    notes: str
    branding: PublicBrandingV1


class CompliancePostalAddressV1(TypedDict, total=False):
    countryCode: str
    city: str
    postalCode: str
    region: str


class ComplianceTaxIdV1(TypedDict, total=False):
    role: TaxIdRole
    schemeId: str
    taxSchemeId: str


class ComplianceTaxRegistrationIdentifierV1(TypedDict, total=False):
    value: str
    taxSchemeId: str


class CompliancePartyV1(TypedDict, total=False):
    postalAddress: CompliancePostalAddressV1
    electronicAddressSchemeId: str
    taxId: ComplianceTaxIdV1
    vatIdentifier: str
    taxRegistrationIdentifier: ComplianceTaxRegistrationIdentifierV1


class _ComplianceLineRequired(TypedDict):
    sourceIndex: int


class ComplianceLineV1(_ComplianceLineRequired, total=False):
    unitCode: str
    vatCategoryCode: VatCategoryCode
    vatExemptionReason: str
    vatExemptionReasonCode: str


class ComplianceSupplementV1(TypedDict, total=False):
    version: Literal[1]
    buyerReference: str
    seller: CompliancePartyV1
    buyer: CompliancePartyV1
    lines: list[ComplianceLineV1]


class _PublicStructuredRequestRequired(TypedDict):
    document: PublicDocumentV1


class PublicStructuredRequestV1(_PublicStructuredRequestRequired, total=False):
    supplement: ComplianceSupplementV1


class ReadinessGapV1(TypedDict):
    id: str
    message: str


class ReadinessResultV1(TypedDict):
    apiVersion: Literal["v1"]
    profileId: str
    specificationIdentifier: str
    ready: bool
    gaps: list[ReadinessGapV1]


class StructuredArtifactV1(TypedDict):
    mediaType: Literal["application/xml"]
    content: str


class StructuredResultV1(ReadinessResultV1):
    artifact: StructuredArtifactV1 | None
