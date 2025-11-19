"""
Database Schemas for the Legal Services CRM

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict


class Customer(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Postal address")
    notes: Optional[str] = Field(None, description="Internal notes")
    status: str = Field("active", description="active | lead | archived")


class Product(BaseModel):
    title: str = Field(..., description="Service name (e.g., Will Writing)")
    description: Optional[str] = Field(None, description="Service details")
    price: float = Field(..., ge=0, description="Base price in currency units")
    category: str = Field("service", description="service | add-on | package")
    in_stock: bool = Field(True, description="Whether available for sale")


class OrderItem(BaseModel):
    product_id: str = Field(..., description="Referenced product id")
    quantity: int = Field(1, ge=1)
    price: float = Field(..., ge=0, description="Unit price at time of order")


class Order(BaseModel):
    customer_id: str = Field(..., description="Referenced customer id")
    items: List[OrderItem] = Field(default_factory=list)
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="pending | paid | completed | cancelled")
    notes: Optional[str] = Field(None)


class FactFind(BaseModel):
    customer_id: str = Field(..., description="Referenced customer id")
    responses: Dict[str, str] = Field(default_factory=dict, description="Q&A map")
    stage: str = Field("new", description="new | in_progress | completed")


class Settings(BaseModel):
    company_name: str = Field("Your Law Firm")
    contact_email: EmailStr = Field("info@example.com")
    currency: str = Field("USD")
    tax_rate: float = Field(0.0, ge=0, le=1, description="Tax rate as decimal, e.g., 0.2 for 20%")
