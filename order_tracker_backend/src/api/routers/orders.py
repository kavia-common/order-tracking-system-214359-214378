from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user, require_admin
from src.db.models import Order, OrderStatusHistory, User, UserRole
from src.db.session import get_db
from src.schemas import (
    OrderCreateRequest,
    OrderDetailResponse,
    OrderResponse,
    OrderStatusHistoryItem,
    OrderStatusUpdateRequest,
    OrderUpdateRequest,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _order_to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        title=order.title,
        description=order.description,
        current_status=order.current_status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _history_item(item: OrderStatusHistory) -> OrderStatusHistoryItem:
    return OrderStatusHistoryItem(
        id=item.id,
        old_status=item.old_status,
        new_status=item.new_status,
        changed_by_user_id=item.changed_by_user_id,
        note=item.note,
        changed_at=item.changed_at,
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order (admin only)",
    description="Create a new order for a specific user_id. Admin-only endpoint.",
)
def create_order(
    payload: OrderCreateRequest,
    user_id: int = Query(..., description="Owner user_id for the order"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> OrderResponse:
    order = Order(order_number=payload.order_number, user_id=user_id, title=payload.title, description=payload.description)
    db.add(order)
    try:
        db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Order number already exists")

    history = OrderStatusHistory(
        order_id=order.id,
        old_status=None,
        new_status=order.current_status,
        changed_by_user_id=None,
    )
    db.add(history)
    db.flush()

    return _order_to_response(order)


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get order details",
    description="Customers can only access their own orders; admins can access any order. Includes status history.",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailResponse:
    order = db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role != UserRole.admin and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    history = db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.changed_at.asc(), OrderStatusHistory.id.asc())
    ).all()
    return OrderDetailResponse(**_order_to_response(order).model_dump(), history=[_history_item(h) for h in history])


@router.get(
    "/lookup/by-number/{order_number}",
    response_model=OrderDetailResponse,
    summary="Lookup order by order number",
    description="Customers can only lookup their own orders; admins can lookup any.",
)
def lookup_by_number(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailResponse:
    order = db.scalar(select(Order).where(Order.order_number == order_number))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role != UserRole.admin and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    history = db.scalars(select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id)).all()
    return OrderDetailResponse(**_order_to_response(order).model_dump(), history=[_history_item(h) for h in history])


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List orders",
    description="Admins get all orders. Customers get their own orders only.",
)
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    if user.role == UserRole.admin:
        orders = db.scalars(select(Order).order_by(Order.created_at.desc())).all()
    else:
        orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())).all()
    return [_order_to_response(o) for o in orders]


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update order details",
    description="Admins can update any order. Customers can update title/description only for their own orders (optional).",
)
def update_order(
    order_id: int,
    payload: OrderUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    order = db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role != UserRole.admin and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if payload.title is not None:
        order.title = payload.title
    if payload.description is not None:
        order.description = payload.description

    db.add(order)
    db.flush()
    return _order_to_response(order)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order (admin only)",
    description="Deletes an order and its status history. Admin-only.",
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    order = db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.flush()
    return None


@router.post(
    "/{order_id}/status",
    response_model=OrderDetailResponse,
    summary="Update order status",
    description="Admins can update any order. Customers cannot update status.",
)
def update_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> OrderDetailResponse:
    order = db.scalar(select(Order).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    old = order.current_status
    order.current_status = payload.new_status
    db.add(order)
    db.flush()

    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old,
        new_status=payload.new_status,
        changed_by_user_id=admin.id,
        note=payload.note,
    )
    db.add(history)
    db.flush()

    history_items = db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.changed_at.asc(), OrderStatusHistory.id.asc())
    ).all()
    return OrderDetailResponse(**_order_to_response(order).model_dump(), history=[_history_item(h) for h in history_items])
