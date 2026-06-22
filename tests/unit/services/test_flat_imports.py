import uuid

import pytest

from app.models import Building, BuildingFloor, Flat, FlatType, User, Wing
from app.schemas.flat_import import FlatImportPreviewInput
from app.services.flat_imports import (
    FlatImportValidationError,
    confirm_flat_import,
    preview_flat_import_rows,
)
from app.tenants.context import TenantContext


class FakeConfirmSession:
    def __init__(
        self,
        *,
        building: Building,
        existing_flats: list[Flat],
        flat_types: list[FlatType],
        floors: list[BuildingFloor],
        wings: list[Wing],
    ) -> None:
        self.building = building
        self.scalar_lists = [existing_flats, flat_types, floors, wings]
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object:
        return self.building

    def scalars(self, *_: object) -> list[object]:
        return self.scalar_lists.pop(0)

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        self.committed = True


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Society Admin",
    )


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=actor,
    )


def build_flat_type(*, code: str, name: str = "Two Bedroom") -> FlatType:
    return FlatType(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        name=name,
        code=code,
        unit_category="residential",
        default_parking_count=1,
        status="active",
    )


def build_floor(*, label: str) -> BuildingFloor:
    return BuildingFloor(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        building_id=uuid.uuid4(),
        floor_label=label,
        floor_number=1,
        status="active",
    )


def build_wing(*, code: str, name: str = "A Wing") -> Wing:
    return Wing(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        building_id=uuid.uuid4(),
        name=name,
        code=code,
        status="active",
    )


def test_preview_flat_import_validates_and_resolves_rows() -> None:
    flat_type = build_flat_type(code="2BHK")
    floor = build_floor(label="First Floor")
    wing = build_wing(code="A")

    preview = preview_flat_import_rows(
        rows=[
            FlatImportPreviewInput(
                flat_number="101",
                flat_type_code="2BHK",
                floor_label="First Floor",
                wing_code="A",
            )
        ],
        existing_flats=[],
        flat_types=[flat_type],
        floors=[floor],
        wings=[wing],
    )

    assert preview.total_rows == 1
    assert preview.valid_rows == 1
    assert preview.invalid_rows == 0
    assert preview.rows[0].resolved.flat_type is not None
    assert preview.rows[0].resolved.flat_type.id == flat_type.id
    assert preview.rows[0].resolved.floor is not None
    assert preview.rows[0].resolved.floor.id == floor.id
    assert preview.rows[0].resolved.wing is not None
    assert preview.rows[0].resolved.wing.id == wing.id


def test_preview_flat_import_rejects_missing_required_values() -> None:
    preview = preview_flat_import_rows(
        rows=[FlatImportPreviewInput()],
        existing_flats=[],
        flat_types=[],
        floors=[],
        wings=[],
    )

    assert preview.valid_rows == 0
    assert preview.invalid_rows == 1
    assert preview.rows[0].errors == [
        "Flat number is required.",
        "Flat type code is required.",
        "Floor label is required.",
    ]


def test_preview_flat_import_rejects_unknown_references() -> None:
    preview = preview_flat_import_rows(
        rows=[
            FlatImportPreviewInput(
                flat_number="101",
                flat_type_code="3BHK",
                floor_label="Third Floor",
                wing_code="Z",
            )
        ],
        existing_flats=[],
        flat_types=[build_flat_type(code="2BHK")],
        floors=[build_floor(label="First Floor")],
        wings=[build_wing(code="A")],
    )

    assert preview.valid_rows == 0
    assert preview.rows[0].errors == [
        "Flat type '3BHK' was not found.",
        "Floor 'Third Floor' was not found.",
        "Wing 'Z' was not found.",
    ]


def test_preview_flat_import_rejects_existing_duplicate_in_same_wing() -> None:
    wing = build_wing(code="A")
    existing_flat = Flat(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        building_id=uuid.uuid4(),
        wing_id=wing.id,
        flat_number="101",
    )

    preview = preview_flat_import_rows(
        rows=[
            FlatImportPreviewInput(
                flat_number="101",
                flat_type_code="2BHK",
                floor_label="First Floor",
                wing_code="A",
            )
        ],
        existing_flats=[existing_flat],
        flat_types=[build_flat_type(code="2BHK")],
        floors=[build_floor(label="First Floor")],
        wings=[wing],
    )

    assert preview.valid_rows == 0
    assert "Flat number already exists for this building and wing." in preview.rows[0].errors


def test_preview_flat_import_rejects_duplicate_inside_import_file() -> None:
    preview = preview_flat_import_rows(
        rows=[
            FlatImportPreviewInput(flat_number="101", flat_type_code="2BHK", floor_label="First Floor"),
            FlatImportPreviewInput(flat_number="101", flat_type_code="2BHK", floor_label="First Floor"),
        ],
        existing_flats=[],
        flat_types=[build_flat_type(code="2BHK")],
        floors=[build_floor(label="First Floor")],
        wings=[],
    )

    assert preview.valid_rows == 1
    assert preview.invalid_rows == 1
    assert "Flat number is duplicated in this import file for the same wing." in preview.rows[1].errors


def test_confirm_flat_import_creates_flats_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    flat_type = build_flat_type(code="2BHK")
    floor = build_floor(label="First Floor")
    wing = build_wing(code="A")
    session = FakeConfirmSession(
        building=building,
        existing_flats=[],
        flat_types=[flat_type],
        floors=[floor],
        wings=[wing],
    )

    result = confirm_flat_import(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        rows=[
            FlatImportPreviewInput(
                flat_number="101",
                flat_type_code="2BHK",
                floor_label="First Floor",
                wing_code="A",
            )
        ],
        actor=actor,
    )

    imported_flat = session.added[0]
    assert isinstance(imported_flat, Flat)
    assert imported_flat.flat_number == "101"
    assert imported_flat.flat_type_id == flat_type.id
    assert imported_flat.floor_id == floor.id
    assert imported_flat.wing_id == wing.id
    assert result.imported_count == 1
    assert result.flat_ids == [imported_flat.id]
    assert session.committed is True
    assert len(session.added) == 2


def test_confirm_flat_import_rejects_invalid_batch_without_commit() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    session = FakeConfirmSession(
        building=building,
        existing_flats=[],
        flat_types=[],
        floors=[],
        wings=[],
    )

    with pytest.raises(FlatImportValidationError) as exc_info:
        confirm_flat_import(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            rows=[FlatImportPreviewInput(flat_number="101", flat_type_code="2BHK")],
            actor=actor,
        )

    assert exc_info.value.preview.invalid_rows == 1
    assert session.committed is False
    assert session.added == []
