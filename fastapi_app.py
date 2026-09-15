"""
Sample FastAPI Application for testing API Documentation Agent.
Contains APIRouter, path parameters, query parameters, Pydantic body schemas, docstrings, and auth dependencies.
"""

from typing import List, Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field

app = FastAPI(title="E-Commerce Store API", version="1.0.0")

# Router definitions
users_router = APIRouter(prefix="/users", tags=["Users"])
products_router = APIRouter(prefix="/products", tags=["Products"])


# Pydantic Schemas
class UserCreate(BaseModel):
    username: str = Field(..., description="Unique user handle")
    email: str = Field(..., description="User primary email address")
    full_name: Optional[str] = Field(None, description="User full legal name")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True


class ProductCreate(BaseModel):
    name: str = Field(..., description="Product display title")
    price: float = Field(..., description="Product unit price in USD")
    category: str = Field("general", description="Product department category")
    in_stock: bool = True


# Auth dependency helper
def verify_token(authorization: str = Header(..., description="Bearer token header")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token scheme")
    return True


@app.get("/health", tags=["System"])
def health_check():
    """
    Returns server uptime status and system metrics.
    """
    return {"status": "healthy", "service": "ecommerce-api"}


@users_router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(20, description="Max items per page"),
    active_only: bool = Query(True, description="Filter active users"),
):
    """
    Retrieve a paginated list of registered users.
    Supports filtering by active status and pagination offsets.
    """
    return [{"id": 1, "username": "alice", "email": "alice@example.com", "is_active": True}]


@users_router.post("/", status_code=201, response_model=UserResponse)
def create_user(user: UserCreate, auth: bool = Depends(verify_token)):
    """
    Register a new user account in the system.
    Requires Bearer authentication.
    """
    return {"id": 2, "username": user.username, "email": user.email, "is_active": True}


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int):
    """
    Fetch detailed user profile information by unique ID.
    """
    return {"id": user_id, "username": "alice", "email": "alice@example.com", "is_active": True}


@products_router.get("/")
def search_products(
    q: Optional[str] = Query(None, description="Search keyword query"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_price: Optional[float] = Query(None, description="Maximum price threshold"),
):
    """
    Search product catalog with dynamic filter parameters.
    """
    return [{"id": 101, "name": "Wireless Headphones", "price": 149.99, "category": "electronics"}]


@products_router.post("/", status_code=201)
def add_product(product: ProductCreate, auth: bool = Depends(verify_token)):
    """
    Add a new product listing to the inventory catalog.
    """
    return {"id": 102, "name": product.name, "price": product.price, "in_stock": True}


@products_router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, auth: bool = Depends(verify_token)):
    """
    Remove a product item from inventory by ID.
    """
    return None


app.include_router(users_router)
app.include_router(products_router)
