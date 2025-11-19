import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Customer, Product, Order, FactFind, Settings

app = FastAPI(title="Legal Services CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ObjectIdStr(BaseModel):
    id: str


def to_str_id(doc: Dict[str, Any]):
    if doc is None:
        return None
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    return d


@app.get("/")
def read_root():
    return {"message": "Legal Services CRM Backend is running"}


@app.get("/schema")
def get_schema():
    return {
        "customer": Customer.model_json_schema(),
        "product": Product.model_json_schema(),
        "order": Order.model_json_schema(),
        "factfind": FactFind.model_json_schema(),
        "settings": Settings.model_json_schema(),
    }


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# CRUD Endpoints
# Customers
@app.post("/customers")
def create_customer(payload: Customer):
    new_id = create_document("customer", payload)
    return {"id": new_id}


@app.get("/customers")
def list_customers(limit: int = 100):
    docs = get_documents("customer", {}, limit)
    return [to_str_id(d) for d in docs]


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        doc = db["customer"].find_one({"_id": ObjectId(customer_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer id")
    if not doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    return to_str_id(doc)


@app.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        res = db["customer"].update_one({"_id": ObjectId(customer_id)}, {"$set": payload})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer id")
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"updated": True}


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        res = db["customer"].delete_one({"_id": ObjectId(customer_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer id")
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"deleted": True}


# Products
@app.post("/products")
def create_product(payload: Product):
    new_id = create_document("product", payload)
    return {"id": new_id}


@app.get("/products")
def list_products(limit: int = 200):
    docs = get_documents("product", {}, limit)
    return [to_str_id(d) for d in docs]


@app.put("/products/{product_id}")
def update_product(product_id: str, payload: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        res = db["product"].update_one({"_id": ObjectId(product_id)}, {"$set": payload})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"updated": True}


# Orders
@app.post("/orders")
def create_order(payload: Order):
    new_id = create_document("order", payload)
    return {"id": new_id}


@app.get("/orders")
def list_orders(limit: int = 200):
    docs = get_documents("order", {}, limit)
    return [to_str_id(d) for d in docs]


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        doc = db["order"].find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return to_str_id(doc)


# FactFind
@app.post("/factfinds")
def create_factfind(payload: FactFind):
    new_id = create_document("factfind", payload)
    return {"id": new_id}


@app.get("/factfinds")
def list_factfinds(limit: int = 200, customer_id: Optional[str] = None):
    filter_dict = {"customer_id": customer_id} if customer_id else {}
    docs = get_documents("factfind", filter_dict, limit)
    return [to_str_id(d) for d in docs]


# Settings
@app.get("/settings")
def get_settings():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["settings"].find_one({})
    if not doc:
        default = Settings().model_dump()
        create_document("settings", default)
        return default
    return to_str_id(doc)


@app.put("/settings")
def update_settings(payload: Settings):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    data = payload.model_dump()
    db["settings"].update_one({}, {"$set": data}, upsert=True)
    return {"updated": True}


# Analytics
@app.get("/analytics/summary")
def analytics_summary():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    customers = db["customer"].count_documents({})
    orders = db["order"].count_documents({})
    revenue = 0.0
    for o in db["order"].find({}, {"total": 1}):
        revenue += float(o.get("total", 0))
    top_products = []
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.product_id", "qty": {"$sum": "$items.quantity"}}},
        {"$sort": {"qty": -1}},
        {"$limit": 5},
    ]
    try:
        top_cursor = db["order"].aggregate(pipeline)
        for t in top_cursor:
            top_products.append({"product_id": t["_id"], "quantity": int(t["qty"])})
    except Exception:
        top_products = []

    return {
        "customers": int(customers),
        "orders": int(orders),
        "revenue": revenue,
        "top_products": top_products,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
