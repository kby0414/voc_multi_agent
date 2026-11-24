"""원본 VOC 등록과 조회 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.voc_repository import DuplicateVOCError, VOCRepository
from app.schemas.voc import (
    CustomerVOCIntake,
    VOCBulkCreate,
    VOCBulkResponse,
    VOCCreate,
    VOCListResponse,
    VOCReceiptResponse,
    VOCResponse,
)
from app.services.intake_service import IntakeService
from app.services.voc_service import VOCService


router = APIRouter(prefix="/vocs", tags=["VOC"])
repository = VOCRepository()
service = VOCService(repository)
intake_service = IntakeService(voc_service=service)


@router.post("", response_model=VOCResponse, status_code=status.HTTP_201_CREATED)
def create_voc(payload: VOCCreate, session: Session = Depends(get_db)) -> VOCResponse:
    try:
        voc = service.create(session, payload)
    except DuplicateVOCError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return VOCResponse.model_validate(voc)


@router.get("", response_model=VOCListResponse)
def list_vocs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
) -> VOCListResponse:
    items = repository.list(session, offset=offset, limit=limit)
    return VOCListResponse(
        total=repository.count(session),
        offset=offset,
        limit=limit,
        items=[VOCResponse.model_validate(item) for item in items],
    )


@router.post("/bulk", response_model=VOCBulkResponse, status_code=status.HTTP_201_CREATED)
def create_vocs_bulk(
    payload: VOCBulkCreate,
    session: Session = Depends(get_db),
) -> VOCBulkResponse:
    created_items: list[VOCResponse] = []
    duplicate_count = 0
    for item in payload.items:
        try:
            voc = service.create(session, item)
        except DuplicateVOCError:
            duplicate_count += 1
            continue
        created_items.append(VOCResponse.model_validate(voc))

    return VOCBulkResponse(
        requested_count=len(payload.items),
        created_count=len(created_items),
        skipped_duplicate_count=duplicate_count,
        items=created_items,
    )


@router.post(
    "/intake",
    response_model=VOCReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="고객 문의 접수와 자동 분석",
)
def receive_customer_voc(
    payload: CustomerVOCIntake,
    session: Session = Depends(get_db),
) -> VOCReceiptResponse:
    result = intake_service.receive_customer_voc(session, payload)
    return VOCReceiptResponse(
        voc_id=result.voc.id,
        receipt_number=result.voc.external_id,
        processing_status=result.processing_status,
        message="문의가 정상적으로 접수되었습니다.",
    )


@router.get("/{voc_id}", response_model=VOCResponse)
def get_voc(voc_id: int, session: Session = Depends(get_db)) -> VOCResponse:
    voc = repository.get(session, voc_id)
    if voc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VOC를 찾을 수 없습니다.",
        )
    return VOCResponse.model_validate(voc)
