import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BuildingFloor, Flat, FlatType, User, Wing
from app.schemas.flat_import import (
    FlatImportConfirmResponse,
    FlatImportPreviewInput,
    FlatImportPreviewResolved,
    FlatImportPreviewResponse,
    FlatImportPreviewRow,
    FlatImportResolvedReference,
)
from app.services.audit import record_audit_log
from app.services.flats import ensure_building_exists
from app.tenants.context import TenantContext


class FlatImportValidationError(Exception):
    def __init__(self, preview: FlatImportPreviewResponse) -> None:
        self.preview = preview
        super().__init__("Flat import has validation errors.")


def normalize_lookup(value: str | None) -> str:
    return (value or "").strip().casefold()


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def reference(id_value: uuid.UUID | None, label: str | None) -> FlatImportResolvedReference:
    return FlatImportResolvedReference(id=id_value, label=label)


def build_optional_lookup(items: list[object], *attributes: str) -> dict[str, object]:
    lookup: dict[str, object] = {}
    for item in items:
        for attribute in attributes:
            key = normalize_lookup(getattr(item, attribute, None))
            if key:
                lookup.setdefault(key, item)
    return lookup


def load_flat_import_context(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> tuple[list[Flat], list[FlatType], list[BuildingFloor], list[Wing]]:
    existing_flats = list(
        session.scalars(
            select(Flat).where(
                Flat.tenant_id == tenant_context.tenant_id,
                Flat.society_id == society_id,
                Flat.building_id == building_id,
            )
        )
    )
    flat_types = list(
        session.scalars(
            select(FlatType).where(
                FlatType.tenant_id == tenant_context.tenant_id,
                FlatType.society_id == society_id,
                FlatType.status == "active",
            )
        )
    )
    floors = list(
        session.scalars(
            select(BuildingFloor).where(
                BuildingFloor.tenant_id == tenant_context.tenant_id,
                BuildingFloor.society_id == society_id,
                BuildingFloor.building_id == building_id,
                BuildingFloor.status == "active",
            )
        )
    )
    wings = list(
        session.scalars(
            select(Wing).where(
                Wing.tenant_id == tenant_context.tenant_id,
                Wing.society_id == society_id,
                Wing.building_id == building_id,
                Wing.status == "active",
            )
        )
    )
    return existing_flats, flat_types, floors, wings


def preview_flat_import_rows(
    *,
    rows: list[FlatImportPreviewInput],
    existing_flats: list[Flat],
    flat_types: list[FlatType],
    floors: list[BuildingFloor],
    wings: list[Wing],
) -> FlatImportPreviewResponse:
    flat_type_lookup = build_optional_lookup(flat_types, "code", "name")
    floor_lookup = build_optional_lookup(floors, "floor_label")
    wing_lookup = build_optional_lookup(wings, "code", "name")
    existing_keys = {
        (str(flat.wing_id) if flat.wing_id else "", normalize_lookup(flat.flat_number))
        for flat in existing_flats
    }
    pending_keys: set[tuple[str, str]] = set()
    preview_rows: list[FlatImportPreviewRow] = []

    for index, row in enumerate(rows, start=1):
        errors: list[str] = []
        flat_number = clean_text(row.flat_number)
        flat_type_key = normalize_lookup(row.flat_type_code)
        floor_key = normalize_lookup(row.floor_label)
        wing_key = normalize_lookup(row.wing_code)

        flat_type = flat_type_lookup.get(flat_type_key) if flat_type_key else None
        floor = floor_lookup.get(floor_key) if floor_key else None
        wing = wing_lookup.get(wing_key) if wing_key else None

        if not flat_number:
            errors.append("Flat number is required.")
        if not flat_type_key:
            errors.append("Flat type code is required.")
        elif flat_type is None:
            errors.append(f"Flat type '{clean_text(row.flat_type_code)}' was not found.")
        if not floor_key:
            errors.append("Floor label is required.")
        elif floor is None:
            errors.append(f"Floor '{clean_text(row.floor_label)}' was not found.")
        if wing_key and wing is None:
            errors.append(f"Wing '{clean_text(row.wing_code)}' was not found.")

        wing_id = getattr(wing, "id", None)
        duplicate_key = (str(wing_id) if wing_id else "", normalize_lookup(flat_number))
        if flat_number and duplicate_key in existing_keys:
            errors.append("Flat number already exists for this building and wing.")
        if flat_number and duplicate_key in pending_keys:
            errors.append("Flat number is duplicated in this import file for the same wing.")
        if not errors and flat_number:
            pending_keys.add(duplicate_key)

        resolved = FlatImportPreviewResolved(
            flat_type=reference(
                getattr(flat_type, "id", None),
                getattr(flat_type, "name", None),
            )
            if flat_type is not None
            else None,
            floor=reference(
                getattr(floor, "id", None),
                getattr(floor, "floor_label", None),
            )
            if floor is not None
            else None,
            wing=reference(
                getattr(wing, "id", None),
                getattr(wing, "name", None),
            )
            if wing is not None
            else None,
        )
        preview_rows.append(
            FlatImportPreviewRow(
                row_number=index,
                input=row,
                status="invalid" if errors else "valid",
                errors=errors,
                resolved=resolved,
            )
        )

    invalid_rows = sum(1 for row in preview_rows if row.status == "invalid")
    return FlatImportPreviewResponse(
        total_rows=len(preview_rows),
        valid_rows=len(preview_rows) - invalid_rows,
        invalid_rows=invalid_rows,
        rows=preview_rows,
    )


def preview_flat_import(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    rows: list[FlatImportPreviewInput],
) -> FlatImportPreviewResponse:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    existing_flats, flat_types, floors, wings = load_flat_import_context(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    return preview_flat_import_rows(
        rows=rows,
        existing_flats=existing_flats,
        flat_types=flat_types,
        floors=floors,
        wings=wings,
    )


def confirm_flat_import(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    rows: list[FlatImportPreviewInput],
    actor: User,
) -> FlatImportConfirmResponse:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    existing_flats, flat_types, floors, wings = load_flat_import_context(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    preview = preview_flat_import_rows(
        rows=rows,
        existing_flats=existing_flats,
        flat_types=flat_types,
        floors=floors,
        wings=wings,
    )
    if preview.invalid_rows:
        raise FlatImportValidationError(preview)

    flat_type_lookup = build_optional_lookup(flat_types, "code", "name")
    floor_lookup = build_optional_lookup(floors, "floor_label")
    wing_lookup = build_optional_lookup(wings, "code", "name")
    imported_flats: list[Flat] = []

    for row in rows:
        flat_type = flat_type_lookup[normalize_lookup(row.flat_type_code)]
        floor = floor_lookup[normalize_lookup(row.floor_label)]
        wing = wing_lookup.get(normalize_lookup(row.wing_code))
        flat = Flat(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            building_id=building_id,
            wing_id=getattr(wing, "id", None),
            floor_id=getattr(floor, "id"),
            flat_type_id=getattr(flat_type, "id"),
            flat_number=clean_text(row.flat_number),
            floor_number=None,
            carpet_area_sqft=getattr(flat_type, "carpet_area_sqft"),
            built_up_area_sqft=getattr(flat_type, "built_up_area_sqft"),
            parking_count=getattr(flat_type, "default_parking_count"),
            status="active",
        )
        session.add(flat)
        imported_flats.append(flat)

    session.flush()
    flat_ids = [flat.id for flat in imported_flats]
    record_audit_log(
        session,
        action="flat.bulk_imported",
        entity_type="Flat",
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Bulk flat import completed: {len(imported_flats)} flats",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "imported_count": len(imported_flats),
            "flat_ids": [str(flat_id) for flat_id in flat_ids],
        },
    )
    session.commit()
    return FlatImportConfirmResponse(imported_count=len(imported_flats), flat_ids=flat_ids)
