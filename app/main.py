from fastapi import FastAPI, Request
from fastapi import UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.database import (
    SessionLocal,
    MasterSessionLocal,
    build_mysql_url,
    reset_tenant_database_url,
    set_tenant_database_url,
)
from fastapi import Form
from fastapi.responses import RedirectResponse
from datetime import date, timedelta
import calendar
import os
import uuid
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi import Form
from typing import List
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from fastapi import Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


class TenantDatabaseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = None
        path = request.url.path
        public_paths = (
            "/company-enter",
            "/login",
            "/switch-company",
            "/static/",
            "/favicon.ico",
        )
        tenant_database_url = request.session.get("tenant_database_url")

        if not tenant_database_url and not any(path == item or path.startswith(item) for item in public_paths):
            return RedirectResponse("/company-enter", status_code=303)

        if tenant_database_url:
            token = set_tenant_database_url(tenant_database_url)

        try:
            return await call_next(request)
        finally:
            if token:
                reset_tenant_database_url(token)


app.add_middleware(TenantDatabaseMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "ManProPlusERP2026@SecretKey"))

app.mount("/static", StaticFiles(directory="app/static"), name="static")

from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.templating import Jinja2Templates

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"])
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)

templates = Jinja2Templates(env=env)


def get_master_content():
    content = {
        "offers": [],
        "updates": [],
    }

    db = MasterSessionLocal()

    try:
        rows = db.execute(text("""
            SELECT content_type, title, message
            FROM saas_announcements
            WHERE status='Active'
            ORDER BY display_order, id DESC
            LIMIT 8
        """)).mappings().all()

        for row in rows:
            item = {
                "title": row["title"],
                "message": row["message"],
            }
            if row["content_type"] == "Offer":
                content["offers"].append(item)
            else:
                content["updates"].append(item)
    except Exception:
        pass
    finally:
        db.close()

    if not content["offers"]:
        content["offers"] = [
            {
                "title": "AI-ready manufacturing ERP",
                "message": "Manage materials, purchase, sales, accounts, payroll and reports in one SaaS platform.",
            }
        ]

    if not content["updates"]:
        content["updates"] = [
            {
                "title": "ManPro Plus",
                "message": "The complete AI-powered manufacturing ERP for growing industries.",
            }
        ]

    return content


def build_tenant_url(company):
    if company.get("database_url"):
        return company["database_url"]

    return build_mysql_url(
        database_name=company["database_name"],
        user=company.get("database_user"),
        password=company.get("database_password"),
        host=company.get("database_host"),
        port=company.get("database_port"),
    )


def get_tenant_by_code(company_code):
    db = MasterSessionLocal()
    normalized_code = (company_code or "").strip().upper()

    try:
        company = db.execute(
            text("""
                SELECT *
                FROM saas_companies
                WHERE company_code=:company_code
                AND status='Active'
                LIMIT 1
            """),
            {"company_code": normalized_code},
        ).mappings().first()

        return dict(company) if company else None
    except Exception:
        return None
    finally:
        db.close()


def selected_company_context(request: Request):
    return {
        "company_code": request.session.get("tenant_company_code", ""),
        "company_name": request.session.get("tenant_company_name", "ManPro Plus"),
        "company_tagline": request.session.get("tenant_company_tagline", "The Complete AI-Powered Manufacturing ERP"),
        "company_logo_url": request.session.get("tenant_company_logo_url", ""),
        "company_banner_url": request.session.get("tenant_company_banner_url", ""),
        "plan_name": request.session.get("tenant_plan_name", ""),
    }


def store_selected_company(request: Request, company):
    request.session["tenant_company_id"] = company["id"]
    request.session["tenant_company_code"] = company["company_code"]
    request.session["tenant_company_name"] = company["company_name"]
    request.session["tenant_company_tagline"] = company.get("tagline") or "The Complete AI-Powered Manufacturing ERP"
    request.session["tenant_company_logo_url"] = company.get("logo_url") or ""
    request.session["tenant_company_banner_url"] = company.get("banner_image_url") or ""
    request.session["tenant_plan_name"] = company.get("plan_name") or "Starter"
    request.session["tenant_database_url"] = build_tenant_url(company)


def require_company_selection(request: Request):
    if not request.session.get("tenant_database_url"):
        return RedirectResponse("/company-enter", status_code=303)
    return None


def clean_database_error(error):
    message = str(error)

    replacements = [
        "Epiclife@cbe32#",
        "Epiclife%40cbe32%23",
    ]

    for item in replacements:
        if item:
            message = message.replace(item, "[hidden]")

    if "Access denied" in message:
        return "Access denied. Check tenant database username, password and database privileges."

    if "Unknown database" in message:
        return "Unknown database. Check tenant database name."

    if "Can't connect" in message or "timed out" in message:
        return "Cannot connect to tenant database host. Check Remote MySQL access and host settings."

    return "Tenant database connection failed. Check database URL, user privileges and remote MySQL access."


def is_admin_user(request: Request):
    return request.session.get("role", "Admin") == "Admin"


def admin_only_redirect(request: Request):
    if not is_admin_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return None


@app.get("/")
async def home(request: Request):

    if "user" in request.session:
        return RedirectResponse("/dashboard", status_code=303)

    if request.session.get("tenant_database_url"):
        return RedirectResponse("/login", status_code=303)

    return RedirectResponse("/company-enter", status_code=303)


@app.get("/company-enter")
async def company_enter_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/dashboard", status_code=303)

    content = get_master_content()

    return templates.TemplateResponse(
        request=request,
        name="company_enter.html",
        context={
            "request": request,
            "error": "",
            "offers": content["offers"],
            "updates": content["updates"],
        },
    )


@app.post("/company-enter")
async def company_enter(
    request: Request,
    company_code: str = Form(...),
):
    company = get_tenant_by_code(company_code)

    if not company:
        content = get_master_content()

        return templates.TemplateResponse(
            request=request,
            name="company_enter.html",
            context={
                "request": request,
                "error": "Company code not found or inactive.",
                "offers": content["offers"],
                "updates": content["updates"],
            },
        )

    request.session.clear()
    store_selected_company(request, company)

    return RedirectResponse("/login", status_code=303)


@app.get("/switch-company")
async def switch_company(request: Request):
    request.session.clear()
    return RedirectResponse("/company-enter", status_code=303)

@app.get("/dashboard")
async def dashboard(request: Request):

    blocked = require_company_selection(request)
    if blocked:
        return blocked

    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()

    today_sales = db.execute(text("""
        SELECT IFNULL(SUM(grand_total),0)
        FROM sales
        WHERE sale_date = CURDATE()
    """)).scalar()

    today_purchase = db.execute(text("""
        SELECT IFNULL(SUM(grand_total),0)
        FROM purchase
        WHERE purchase_date = CURDATE()
    """)).scalar()

    month_sales = db.execute(text("""
        SELECT IFNULL(SUM(grand_total),0)
        FROM sales
        WHERE MONTH(sale_date) = MONTH(CURDATE())
        AND YEAR(sale_date) = YEAR(CURDATE())
    """)).scalar()

    month_purchase = db.execute(text("""
        SELECT IFNULL(SUM(grand_total),0)
        FROM purchase
        WHERE MONTH(purchase_date) = MONTH(CURDATE())
        AND YEAR(purchase_date) = YEAR(CURDATE())
    """)).scalar()

    has_supplier_payments = db.execute(text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = 'supplier_payments'
    """)).scalar()

    has_customer_payments = db.execute(text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = 'customer_payments'
    """)).scalar()

    if has_supplier_payments:
        pending_supplier = db.execute(text("""
            SELECT
                IFNULL(p.purchase_amount,0) - IFNULL(pay.paid_amount,0)
            FROM
            (
                SELECT IFNULL(SUM(grand_total),0) AS purchase_amount
                FROM purchase
            ) p
            CROSS JOIN
            (
                SELECT IFNULL(SUM(amount),0) AS paid_amount
                FROM supplier_payments
            ) pay
        """)).scalar()
    else:
        pending_supplier = 0

    if has_customer_payments:
        pending_customer = db.execute(text("""
            SELECT
                IFNULL(s.sale_amount,0) - IFNULL(pay.received_amount,0)
            FROM
            (
                SELECT IFNULL(SUM(grand_total),0) AS sale_amount
                FROM sales
            ) s
            CROSS JOIN
            (
                SELECT IFNULL(SUM(amount),0) AS received_amount
                FROM customer_payments
            ) pay
        """)).scalar()
    else:
        pending_customer = 0

    recent_sales = db.execute(text("""
        SELECT
            s.invoice_number,
            s.sale_date,
            c.customer_name,
            s.grand_total
        FROM sales s
        LEFT JOIN customers c
            ON c.id = s.customer_id
        ORDER BY s.sale_date DESC, s.id DESC
        LIMIT 5
    """)).mappings().all()

    recent_purchases = db.execute(text("""
        SELECT
            p.purchase_no,
            p.purchase_date,
            s.supplier_name,
            p.grand_total
        FROM purchase p
        LEFT JOIN suppliers s
            ON s.id = p.supplier_id
        ORDER BY p.purchase_date DESC, p.purchase_id DESC
        LIMIT 5
    """)).mappings().all()

    sales_chart = db.execute(text("""
        SELECT
            DATE_FORMAT(sale_date, '%b') AS month_name,
            MONTH(sale_date) AS month_no,
            IFNULL(SUM(grand_total),0) AS sale_amount
        FROM sales
        WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
        GROUP BY YEAR(sale_date), MONTH(sale_date), DATE_FORMAT(sale_date, '%b')
        ORDER BY YEAR(sale_date), MONTH(sale_date)
    """)).mappings().all()

    sales_chart_labels = [row["month_name"] for row in sales_chart]
    sales_chart_values = [float(row["sale_amount"] or 0) for row in sales_chart]

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "username": request.session["user"],
            "full_name": request.session.get("full_name", request.session["user"]),
            "role": request.session.get("role", "Admin"),
            "today_sales": today_sales or 0,
            "today_purchase": today_purchase or 0,
            "month_sales": month_sales or 0,
            "month_purchase": month_purchase or 0,
            "pending_supplier": pending_supplier or 0,
            "pending_customer": pending_customer or 0,
            "recent_sales": recent_sales,
            "recent_purchases": recent_purchases,
            "sales_chart_labels": sales_chart_labels,
            "sales_chart_values": sales_chart_values,
        }
    )


@app.get("/company")
def company(request: Request):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    db = SessionLocal()

    company = db.execute(text("SELECT * FROM company LIMIT 1")).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="company.html", context={"company": company}
    )


@app.post("/company/save")
def save_company(
    request: Request,
    company_name: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    gst_number: str = Form(...),
):

    db = SessionLocal()

    existing = db.execute(text("SELECT id FROM company LIMIT 1")).fetchone()

    if existing:

        db.execute(
            text("""
                UPDATE company
                SET
                    company_name=:company_name,
                    address=:address,
                    city=:city,
                    state=:state,
                    pincode=:pincode,
                    phone=:phone,
                    email=:email,
                    gst_number=:gst_number
            """),
            {
                "company_name": company_name,
                "address": address,
                "city": city,
                "state": state,
                "pincode": pincode,
                "phone": phone,
                "email": email,
                "gst_number": gst_number,
            },
        )

    else:

        db.execute(
            text("""
                INSERT INTO company
                (
                    company_name,
                    address,
                    city,
                    state,
                    pincode,
                    phone,
                    email,
                    gst_number
                )
                VALUES
                (
                    :company_name,
                    :address,
                    :city,
                    :state,
                    :pincode,
                    :phone,
                    :email,
                    :gst_number
                )
            """),
            {
                "company_name": company_name,
                "address": address,
                "city": city,
                "state": state,
                "pincode": pincode,
                "phone": phone,
                "email": email,
                "gst_number": gst_number,
            },
        )

    db.commit()
    db.close()

    return RedirectResponse(url="/company", status_code=303)


@app.get("/raw-materials")
def raw_materials(request: Request):

    db = SessionLocal()

    materials = db.execute(text("""
            SELECT *
            FROM raw_materials
            ORDER BY material_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request, name="raw_materials.html", context={"materials": materials}
    )


@app.get("/raw-material/add")
def add_material(request: Request):

    return templates.TemplateResponse(request=request, name="raw_material_form.html")


@app.post("/raw-material/save")
def save_material(
    material_name: str = Form(""),
    unit: str = Form(""),
    purchase_price: float = Form(0),
    stock_qty: float = Form(0),
    minimum_stock: float = Form(0),
    gst_percent: float = Form(0),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO raw_materials
            (
                material_name,
                unit,
                purchase_price,
                stock_qty,
                minimum_stock,
                gst_percent
            )
            VALUES
            (
                :material_name,
                :unit,
                :purchase_price,
                :stock_qty,
                :minimum_stock,
                :gst_percent
            )
        """),
        {
            "material_name": material_name,
            "unit": unit,
            "purchase_price": purchase_price,
            "stock_qty": stock_qty,
            "minimum_stock": minimum_stock,
            "gst_percent": gst_percent,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/raw-materials", status_code=303)


@app.get("/raw-material/delete/{material_id}")
def delete_material(material_id: int):

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM raw_materials
            WHERE id = :id
        """),
        {"id": material_id},
    )

    db.commit()
    db.close()

    return RedirectResponse("/raw-materials", status_code=303)


@app.get("/products")
def products(request: Request):

    db = SessionLocal()

    products = db.execute(text("""
            SELECT *
            FROM products
            ORDER BY product_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request, name="products.html", context={"products": products}
    )


@app.get("/product/add")
def product_add(request: Request):

    return templates.TemplateResponse(request=request, name="product_form.html")


@app.post("/product/save")
def save_product(
    product_name: str = Form(""),
    product_code: str = Form(""),
    product_type: str = Form(""),
    size: str = Form(""),
    gsm: str = Form(""),
    color: str = Form(""),
    hsn_code: str = Form(""),
    gst_percent: float = Form(0),
    purchase_price: float = Form(0),
    sale_price: float = Form(0),
    category: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO products
            (
                product_name,
                product_code,
                product_type,
                size,
                gsm,
                color,
                hsn_code,
                gst_percent,
                purchase_price,
                sale_price,
                category
            )
            VALUES
            (
                :product_name,
                :product_code,
                :product_type,
                :size,
                :gsm,
                :color,
                :hsn_code,
                :gst_percent,
                :purchase_price,
                :sale_price,
                :category
            )
        """),
        {
            "product_name": product_name,
            "product_code": product_code,
            "product_type": product_type,
            "size": size,
            "gsm": gsm,
            "color": color,
            "hsn_code": hsn_code,
            "gst_percent": gst_percent,
            "purchase_price": purchase_price,
            "sale_price": sale_price,
            "category": category,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/products", status_code=303)


@app.get("/product/delete/{product_id}")
def delete_product(product_id: int):

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM products
            WHERE id = :id
        """),
        {"id": product_id},
    )

    db.commit()
    db.close()

    return RedirectResponse(url="/products", status_code=303)


@app.get("/suppliers")
def suppliers(request: Request):

    db = SessionLocal()

    suppliers = db.execute(text("""
            SELECT *
            FROM suppliers
            ORDER BY supplier_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request, name="suppliers.html", context={"suppliers": suppliers}
    )


@app.get("/supplier/add")
def supplier_add(request: Request):

    return templates.TemplateResponse(request=request, name="supplier_form.html")


@app.post("/supplier/save")
def supplier_save(
    supplier_name: str = Form(""),
    company_name: str = Form(""),
    gst_number: str = Form(""),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    state: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO suppliers
            (
                supplier_name,
                company_name,
                gst_number,
                phone,
                mobile,
                email,
                address,
                state
            )
            VALUES
            (
                :supplier_name,
                :company_name,
                :gst_number,
                :phone,
                :mobile,
                :email,
                :address,
                :state
            )
        """),
        {
            "supplier_name": supplier_name,
            "company_name": company_name,
            "gst_number": gst_number,
            "phone": phone,
            "mobile": mobile,
            "email": email,
            "address": address,
            "state": state,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/suppliers", status_code=303)


@app.get("/supplier/delete/{supplier_id}")
def delete_supplier(supplier_id: int):

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM suppliers
            WHERE id = :id
        """),
        {"id": supplier_id},
    )

    db.commit()
    db.close()

    return RedirectResponse("/suppliers", status_code=303)


@app.get("/customers")
def customers(request: Request):

    db = SessionLocal()

    customers = db.execute(text("""
            SELECT *
            FROM customers
            ORDER BY customer_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request, name="customers.html", context={"customers": customers}
    )


@app.get("/customer/add")
def customer_add(request: Request):

    return templates.TemplateResponse(request=request, name="customer_form.html")


@app.post("/customer/save")
def customer_save(
    customer_name: str = Form(""),
    company_name: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    gst_number: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO customers
            (
                customer_name,
                company_name,
                mobile,
                email,
                address,
                gst_number
            )
            VALUES
            (
                :customer_name,
                :company_name,
                :mobile,
                :email,
                :address,
                :gst_number
            )
        """),
        {
            "customer_name": customer_name,
            "company_name": company_name,
            "mobile": mobile,
            "email": email,
            "address": address,
            "gst_number": gst_number,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/customers", status_code=303)


@app.get("/customer/delete/{customer_id}")
def delete_customer(customer_id: int):

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM customers
            WHERE id=:id
        """),
        {"id": customer_id},
    )

    db.commit()
    db.close()

    return RedirectResponse("/customers", status_code=303)


@app.get("/raw-material/edit/{material_id}")
def edit_material(material_id: int, request: Request):

    db = SessionLocal()

    material = db.execute(
        text("""
            SELECT *
            FROM raw_materials
            WHERE id=:id
        """),
        {"id": material_id},
    ).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="raw_material_edit.html", context={"material": material}
    )


@app.post("/raw-material/update")
def update_material(
    id: int = Form(...),
    material_name: str = Form(""),
    unit: str = Form(""),
    purchase_price: float = Form(0),
    stock_qty: float = Form(0),
    minimum_stock: float = Form(0),
    gst_percent: float = Form(0),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE raw_materials
            SET
                material_name=:material_name,
                unit=:unit,
                purchase_price=:purchase_price,
                stock_qty=:stock_qty,
                minimum_stock=:minimum_stock,
                gst_percent=:gst_percent
            WHERE id=:id
        """),
        {
            "id": id,
            "material_name": material_name,
            "unit": unit,
            "purchase_price": purchase_price,
            "stock_qty": stock_qty,
            "minimum_stock": minimum_stock,
            "gst_percent": gst_percent,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/raw-materials", status_code=303)


@app.get("/product/edit/{product_id}")
def edit_product(product_id: int, request: Request):

    db = SessionLocal()

    product = db.execute(
        text("""
            SELECT *
            FROM products
            WHERE id=:id
        """),
        {"id": product_id},
    ).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="products_edit.html", context={"product": product}
    )


@app.post("/product/update")
def update_product(
    id: int = Form(...),
    product_name: str = Form(""),
    product_code: str = Form(""),
    product_type: str = Form(""),
    size: str = Form(""),
    gsm: str = Form(""),
    color: str = Form(""),
    hsn_code: str = Form(""),
    gst_percent: float = Form(0),
    purchase_price: float = Form(0),
    sale_price: float = Form(0),
    category: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE products
            SET
                product_name=:product_name,
                product_code=:product_code,
                product_type=:product_type,
                size=:size,
                gsm=:gsm,
                color=:color,
                hsn_code=:hsn_code,
                gst_percent=:gst_percent,
                purchase_price=:purchase_price,
                sale_price=:sale_price,
                category=:category
            WHERE id=:id
        """),
        {
            "id": id,
            "product_name": product_name,
            "product_code": product_code,
            "product_type": product_type,
            "size": size,
            "gsm": gsm,
            "color": color,
            "hsn_code": hsn_code,
            "gst_percent": gst_percent,
            "purchase_price": purchase_price,
            "sale_price": sale_price,
            "category": category,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/products", status_code=303)


@app.get("/supplier/edit/{supplier_id}")
def edit_supplier(supplier_id: int, request: Request):

    db = SessionLocal()

    supplier = db.execute(
        text("""
            SELECT *
            FROM suppliers
            WHERE id=:id
        """),
        {"id": supplier_id},
    ).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="suppliers_edit.html", context={"supplier": supplier}
    )


@app.post("/supplier/update")
def update_supplier(
    id: int = Form(...),
    supplier_name: str = Form(""),
    company_name: str = Form(""),
    gst_number: str = Form(""),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    state: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE suppliers
            SET
                supplier_name=:supplier_name,
                company_name=:company_name,
                gst_number=:gst_number,
                phone=:phone,
                mobile=:mobile,
                email=:email,
                address=:address,
                state=:state
            WHERE id=:id
        """),
        {
            "id": id,
            "supplier_name": supplier_name,
            "company_name": company_name,
            "gst_number": gst_number,
            "phone": phone,
            "mobile": mobile,
            "email": email,
            "address": address,
            "state": state,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/suppliers", status_code=303)


@app.get("/customer/edit/{customer_id}")
def edit_customer(customer_id: int, request: Request):

    db = SessionLocal()

    customer = db.execute(
        text("""
            SELECT *
            FROM customers
            WHERE id=:id
        """),
        {"id": customer_id},
    ).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="customers_edit.html", context={"customer": customer}
    )


@app.post("/customer/update")
def update_customer(
    id: int = Form(...),
    customer_name: str = Form(""),
    company_name: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    gst_number: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE customers
            SET
                customer_name=:customer_name,
                company_name=:company_name,
                mobile=:mobile,
                email=:email,
                address=:address,
                gst_number=:gst_number
            WHERE id=:id
        """),
        {
            "id": id,
            "customer_name": customer_name,
            "company_name": company_name,
            "mobile": mobile,
            "email": email,
            "address": address,
            "gst_number": gst_number,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/customers", status_code=303)


@app.get("/purchase", response_class=HTMLResponse)
async def purchase_page(request: Request, from_date: str = None, to_date: str = None):

    db = SessionLocal()

    if not from_date:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    if not to_date:
        to_date = date.today().strftime("%Y-%m-%d")

    purchases = (
        db.execute(
            text("""
    SELECT
        p.purchase_id,
        p.purchase_no,
        p.purchase_date,
        s.supplier_name,
        p.invoice_no,
        p.grand_total
    FROM purchase p
    LEFT JOIN suppliers s
        ON p.supplier_id = s.id
    WHERE p.purchase_date
        BETWEEN :from_date AND :to_date
    ORDER BY p.purchase_date DESC,
             p.purchase_id DESC
"""),
            {"from_date": from_date, "to_date": to_date},
        )
        .mappings()
        .all()
    )

    purchase_summary = (
        db.execute(
            text("""
        SELECT
            COUNT(*) AS purchase_count,
            IFNULL(SUM(grand_total),0) AS purchase_amount
        FROM purchase
        WHERE purchase_date
            BETWEEN :from_date AND :to_date
    """),
            {"from_date": from_date, "to_date": to_date},
        )
        .mappings()
        .first()
    )

    supplier_count = db.execute(text("""
        SELECT COUNT(*) AS total
        FROM suppliers
    """)).scalar()

    today_amount = db.execute(text("""
        SELECT
            IFNULL(SUM(grand_total),0)
        FROM purchase
        WHERE purchase_date = CURDATE()
    """)).scalar()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="purchase.html",
        context={
            "purchases": purchases,
            "purchase_count": purchase_summary["purchase_count"],
            "purchase_amount": purchase_summary["purchase_amount"],
            "supplier_count": supplier_count,
            "today_amount": today_amount,
            "from_date": from_date,
            "to_date": to_date,
        },
    )


@app.get("/purchase/add")
def purchase_add(request: Request):

    db = SessionLocal()

    suppliers = db.execute(text("""
            SELECT
                id,
                supplier_name
            FROM suppliers
            ORDER BY supplier_name
        """)).fetchall()

    materials = db.execute(text("""
            SELECT
                id,
                material_name,
                gst_percent,
                purchase_price
            FROM raw_materials
            ORDER BY material_name
        """)).fetchall()

    # Generate Purchase Number

    last_purchase = db.execute(text("""
            SELECT purchase_no
            FROM purchase
            ORDER BY purchase_id DESC
            LIMIT 1
        """)).fetchone()

    if last_purchase:

        last_no = int(last_purchase.purchase_no.replace("PUR", ""))

        purchase_no = f"PUR{last_no + 1:06d}"

    else:

        purchase_no = "PUR000001"

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="purchase_add.html",
        context={
            "suppliers": suppliers,
            "materials": materials,
            "purchase_no": purchase_no,
            "today": date.today().strftime("%Y-%m-%d"),
        },
    )


@app.post("/purchase/save")
async def purchase_save(request: Request):

    form = await request.form()

    purchase_no = form.get("purchase_no")
    purchase_date = form.get("purchase_date")
    supplier_id = int(form.get("supplier_id"))
    invoice_no = form.get("invoice_no", "")
    invoice_date = form.get("invoice_date", "")

    material_id = form.getlist("material_id")
    qty = form.getlist("qty")
    rate = form.getlist("rate")
    gst_percent = form.getlist("gst_percent")
    gst_amount = form.getlist("gst_amount")
    line_total = form.getlist("line_total")

    db = SessionLocal()

    grand_total = sum(float(x or 0) for x in line_total)

    result = db.execute(
        text("""
            INSERT INTO purchase
            (
                purchase_no,
                purchase_date,
                supplier_id,
                invoice_no,
                invoice_date,
                grand_total
            )
            VALUES
            (
                :purchase_no,
                :purchase_date,
                :supplier_id,
                :invoice_no,
                :invoice_date,
                :grand_total
            )
        """),
        {
            "purchase_no": purchase_no,
            "purchase_date": purchase_date,
            "supplier_id": supplier_id,
            "invoice_no": invoice_no,
            "invoice_date": invoice_date if invoice_date else None,
            "grand_total": grand_total,
        },
    )

    purchase_id = result.lastrowid

    for i in range(len(material_id)):

        if not material_id[i]:
            continue

        db.execute(
            text("""
                INSERT INTO purchase_items
                (
                    purchase_id,
                    material_id,
                    quantity,
                    unit_price,
                    gst_percent,
                    gst_amount,
                    line_total
                )
                VALUES
                (
                    :purchase_id,
                    :material_id,
                    :quantity,
                    :unit_price,
                    :gst_percent,
                    :gst_amount,
                    :line_total
                )
            """),
            {
                "purchase_id": purchase_id,
                "material_id": int(material_id[i]),
                "quantity": float(qty[i]),
                "unit_price": float(rate[i]),
                "gst_percent": float(gst_percent[i]),
                "gst_amount": float(gst_amount[i]),
                "line_total": float(line_total[i]),
            },
        )

        db.execute(
            text("""
                UPDATE raw_materials
                SET stock_qty = stock_qty + :qty
                WHERE id = :material_id
            """),
            {"qty": float(qty[i]), "material_id": int(material_id[i])},
        )

    db.commit()
    db.close()

    return RedirectResponse(url="/purchase", status_code=303)


@app.get("/purchase/delete/{purchase_id}")
def purchase_delete(purchase_id: int):

    db = SessionLocal()

    # Delete items first
    db.execute(
        text("""
            DELETE FROM purchase_items
            WHERE purchase_id = :purchase_id
        """),
        {"purchase_id": purchase_id},
    )

    # Delete header
    db.execute(
        text("""
            DELETE FROM purchase
            WHERE purchase_id = :purchase_id
        """),
        {"purchase_id": purchase_id},
    )

    db.commit()
    db.close()

    return RedirectResponse(url="/purchase", status_code=303)


@app.get("/purchase/edit/{purchase_id}")
def purchase_edit(purchase_id: int, request: Request):

    db = SessionLocal()

    purchase = (
        db.execute(
            text("""
            SELECT *
            FROM purchase
            WHERE purchase_id=:purchase_id
        """),
            {"purchase_id": purchase_id},
        )
        .mappings()
        .first()
    )

    items = (
        db.execute(
            text("""
            SELECT *
            FROM purchase_items
            WHERE purchase_id=:purchase_id
        """),
            {"purchase_id": purchase_id},
        )
        .mappings()
        .all()
    )

    suppliers = db.execute(text("""
            SELECT id,supplier_name
            FROM suppliers
            ORDER BY supplier_name
        """)).fetchall()

    materials = db.execute(text("""
            SELECT
                id,
                material_name,
                gst_percent,
                purchase_price
            FROM raw_materials
            ORDER BY material_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="purchase_edit.html",
        context={
            "purchase": purchase,
            "items": items,
            "suppliers": suppliers,
            "materials": materials,
        },
    )

    from fastapi import Request


from fastapi.responses import RedirectResponse


@app.post("/purchase/update")
async def purchase_update(request: Request):

    form = await request.form()

    purchase_id = int(form.get("purchase_id"))

    purchase_no = form.get("purchase_no")
    purchase_date = form.get("purchase_date")
    supplier_id = int(form.get("supplier_id"))
    invoice_no = form.get("invoice_no", "")
    invoice_date = form.get("invoice_date", "")

    material_id = form.getlist("material_id")
    qty = form.getlist("qty")
    rate = form.getlist("rate")
    gst_percent = form.getlist("gst_percent")
    gst_amount = form.getlist("gst_amount")
    line_total = form.getlist("line_total")

    db = SessionLocal()

    # ----------------------------
    # Reverse Previous Stock
    # ----------------------------

    old_items = db.execute(
        text("""
            SELECT
                material_id,
                quantity
            FROM purchase_items
            WHERE purchase_id=:purchase_id
        """),
        {"purchase_id": purchase_id},
    ).fetchall()

    for item in old_items:

        db.execute(
            text("""
                UPDATE raw_materials
                SET stock_qty =
                    stock_qty - :qty
                WHERE id=:material_id
            """),
            {"qty": item.quantity, "material_id": item.material_id},
        )

    # ----------------------------
    # Delete Old Items
    # ----------------------------

    db.execute(
        text("""
            DELETE FROM purchase_items
            WHERE purchase_id=:purchase_id
        """),
        {"purchase_id": purchase_id},
    )

    # ----------------------------
    # Calculate Total
    # ----------------------------

    grand_total = sum(float(x or 0) for x in line_total)

    # ----------------------------
    # Update Header
    # ----------------------------

    db.execute(
        text("""
            UPDATE purchase
            SET
                purchase_date=:purchase_date,
                supplier_id=:supplier_id,
                invoice_no=:invoice_no,
                invoice_date=:invoice_date,
                grand_total=:grand_total
            WHERE purchase_id=:purchase_id
        """),
        {
            "purchase_id": purchase_id,
            "purchase_date": purchase_date,
            "supplier_id": supplier_id,
            "invoice_no": invoice_no,
            "invoice_date": invoice_date if invoice_date else None,
            "grand_total": grand_total,
        },
    )

    # ----------------------------
    # Save New Items
    # ----------------------------

    for i in range(len(material_id)):

        if not material_id[i]:
            continue

        db.execute(
            text("""
                INSERT INTO purchase_items
                (
                    purchase_id,
                    material_id,
                    quantity,
                    unit_price,
                    gst_percent,
                    gst_amount,
                    line_total
                )
                VALUES
                (
                    :purchase_id,
                    :material_id,
                    :quantity,
                    :unit_price,
                    :gst_percent,
                    :gst_amount,
                    :line_total
                )
            """),
            {
                "purchase_id": purchase_id,
                "material_id": int(material_id[i]),
                "quantity": float(qty[i]),
                "unit_price": float(rate[i]),
                "gst_percent": float(gst_percent[i]),
                "gst_amount": float(gst_amount[i]),
                "line_total": float(line_total[i]),
            },
        )

        # Add Stock Again

        db.execute(
            text("""
                UPDATE raw_materials
                SET stock_qty =
                    stock_qty + :qty
                WHERE id=:material_id
            """),
            {"qty": float(qty[i]), "material_id": int(material_id[i])},
        )

    db.commit()
    db.close()

    return RedirectResponse("/purchase", status_code=303)


@app.get("/sales")
def sales_page(request: Request, from_date: str = None, to_date: str = None):

    db = SessionLocal()

    if not from_date:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    if not to_date:
        to_date = date.today().strftime("%Y-%m-%d")

    sales = (
        db.execute(
            text("""
            SELECT
                s.id,
                s.invoice_number,
                s.sale_date,
                c.customer_name,
                s.grand_total
            FROM sales s
            LEFT JOIN customers c
                ON s.customer_id = c.id
            WHERE s.sale_date
                BETWEEN :from_date AND :to_date
            ORDER BY s.id DESC
        """),
            {"from_date": from_date, "to_date": to_date},
        )
        .mappings()
        .all()
    )

    summary = (
        db.execute(
            text("""
            SELECT
                COUNT(*) sale_count,
                IFNULL(SUM(grand_total),0) sale_amount
            FROM sales
            WHERE sale_date
                BETWEEN :from_date AND :to_date
        """),
            {"from_date": from_date, "to_date": to_date},
        )
        .mappings()
        .first()
    )

    customer_count = db.execute(text("""
            SELECT COUNT(*)
            FROM customers
        """)).scalar()

    today_sales = db.execute(text("""
            SELECT
                IFNULL(SUM(grand_total),0)
            FROM sales
            WHERE sale_date = CURDATE()
        """)).scalar()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sales.html",
        context={
            "sales": sales,
            "sale_count": summary["sale_count"],
            "sale_amount": summary["sale_amount"],
            "customer_count": customer_count,
            "today_sales": today_sales,
            "from_date": from_date,
            "to_date": to_date,
        },
    )


@app.get("/sales/add")
def sales_add(request: Request):

    db = SessionLocal()

    customers = db.execute(text("""
            SELECT
                id,
                customer_name
            FROM customers
            ORDER BY customer_name
        """)).fetchall()

    products = db.execute(text("""
            SELECT
                id,
                product_name,
                sale_price,
                gst_percent,
                stock_qty
            FROM products
            ORDER BY product_name
        """)).fetchall()

    last_sale = db.execute(text("""
            SELECT invoice_number
            FROM sales
            ORDER BY id DESC
            LIMIT 1
        """)).fetchone()

    if last_sale:

        try:
            last_no = int(last_sale.invoice_number.replace("SAL", ""))

            invoice_number = f"SAL{last_no+1:06d}"

        except:

            invoice_number = "SAL000001"

    else:

        invoice_number = "SAL000001"

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sales_add.html",
        context={
            "customers": customers,
            "products": products,
            "invoice_number": invoice_number,
            "today": date.today().strftime("%Y-%m-%d"),
        },
    )


@app.post("/sales/save")
async def sales_save(request: Request):

    form = await request.form()

    invoice_number = form.get("invoice_number")
    sale_date = form.get("sale_date")
    customer_id = int(form.get("customer_id"))

    product_id = form.getlist("product_id")
    qty = form.getlist("qty")
    rate = form.getlist("rate")
    gst_percent = form.getlist("gst_percent")
    gst_amount = form.getlist("gst_amount")
    line_total = form.getlist("line_total")

    db = SessionLocal()

    total_amount = 0
    total_gst = 0
    grand_total = 0

    for i in range(len(product_id)):

        total_amount += float(qty[i]) * float(rate[i])

        total_gst += float(gst_amount[i])

        grand_total += float(line_total[i])

    # ==================================
    # SAVE SALES HEADER
    # ==================================

    result = db.execute(
        text("""
            INSERT INTO sales
            (
                invoice_number,
                sale_date,
                customer_id,
                total_amount,
                gst_amount,
                grand_total,
                created_at
            )
            VALUES
            (
                :invoice_number,
                :sale_date,
                :customer_id,
                :total_amount,
                :gst_amount,
                :grand_total,
                NOW()
            )
        """),
        {
            "invoice_number": invoice_number,
            "sale_date": sale_date,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "gst_amount": total_gst,
            "grand_total": grand_total,
        },
    )

    sale_id = result.lastrowid

    # ==================================
    # SAVE SALES ITEMS
    # ==================================

    for i in range(len(product_id)):

        if not product_id[i]:
            continue

        db.execute(
            text("""
                INSERT INTO sale_items
                (
                    sale_id,
                    product_id,
                    quantity,
                    price,
                    total
                )
                VALUES
                (
                    :sale_id,
                    :product_id,
                    :quantity,
                    :price,
                    :total
                )
            """),
            {
                "sale_id": sale_id,
                "product_id": int(product_id[i]),
                "quantity": float(qty[i]),
                "price": float(rate[i]),
                "total": float(line_total[i]),
            },
        )

        # ==========================
        # REDUCE STOCK
        # ==========================

        db.execute(
            text("""
                UPDATE products
                SET stock_qty =
                    stock_qty - :qty
                WHERE id = :product_id
            """),
            {"qty": float(qty[i]), "product_id": int(product_id[i])},
        )

    db.commit()
    db.close()

    return RedirectResponse(url="/sales", status_code=303)


@app.get("/sales/edit/{sale_id}")
def sales_edit(sale_id: int, request: Request):

    db = SessionLocal()

    sale = (
        db.execute(
            text("""
            SELECT *
            FROM sales
            WHERE id=:sale_id
        """),
            {"sale_id": sale_id},
        )
        .mappings()
        .first()
    )

    items = (
        db.execute(
            text("""
            SELECT *
            FROM sale_items
            WHERE sale_id=:sale_id
        """),
            {"sale_id": sale_id},
        )
        .mappings()
        .all()
    )

    customers = db.execute(text("""
            SELECT
                id,
                customer_name
            FROM customers
            ORDER BY customer_name
        """)).fetchall()

    products = db.execute(text("""
            SELECT
                id,
                product_name,
                sale_price,
                gst_percent,
                stock_qty
            FROM products
            ORDER BY product_name
        """)).fetchall()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sales_edit.html",
        context={
            "sale": sale,
            "items": items,
            "customers": customers,
            "products": products,
        },
    )


@app.post("/sales/update")
async def sales_update(request: Request):

    form = await request.form()

    sale_id = int(form.get("sale_id"))

    invoice_number = form.get("invoice_number")
    sale_date = form.get("sale_date")
    customer_id = int(form.get("customer_id"))

    product_id = form.getlist("product_id")
    qty = form.getlist("qty")
    rate = form.getlist("rate")
    gst_percent = form.getlist("gst_percent")
    gst_amount = form.getlist("gst_amount")
    line_total = form.getlist("line_total")

    db = SessionLocal()

    # ==================================
    # RESTORE OLD STOCK
    # ==================================

    old_items = db.execute(
        text("""
            SELECT
                product_id,
                quantity
            FROM sale_items
            WHERE sale_id=:sale_id
        """),
        {"sale_id": sale_id},
    ).fetchall()

    for item in old_items:

        db.execute(
            text("""
                UPDATE products
                SET stock_qty =
                    stock_qty + :qty
                WHERE id=:product_id
            """),
            {"qty": item.quantity, "product_id": item.product_id},
        )

    # ==================================
    # DELETE OLD ITEMS
    # ==================================

    db.execute(
        text("""
            DELETE FROM sale_items
            WHERE sale_id=:sale_id
        """),
        {"sale_id": sale_id},
    )

    # ==================================
    # TOTALS
    # ==================================

    total_amount = 0
    total_gst = 0
    grand_total = 0

    for i in range(len(product_id)):

        total_amount += float(qty[i]) * float(rate[i])

        total_gst += float(gst_amount[i])

        grand_total += float(line_total[i])

    # ==================================
    # UPDATE HEADER
    # ==================================

    db.execute(
        text("""
            UPDATE sales
            SET
                sale_date=:sale_date,
                customer_id=:customer_id,
                total_amount=:total_amount,
                gst_amount=:gst_amount,
                grand_total=:grand_total
            WHERE id=:sale_id
        """),
        {
            "sale_id": sale_id,
            "sale_date": sale_date,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "gst_amount": total_gst,
            "grand_total": grand_total,
        },
    )

    # ==================================
    # SAVE NEW ITEMS
    # ==================================

    for i in range(len(product_id)):

        if not product_id[i]:
            continue

        db.execute(
            text("""
                INSERT INTO sale_items
                (
                    sale_id,
                    product_id,
                    quantity,
                    price,
                    total
                )
                VALUES
                (
                    :sale_id,
                    :product_id,
                    :quantity,
                    :price,
                    :total
                )
            """),
            {
                "sale_id": sale_id,
                "product_id": int(product_id[i]),
                "quantity": float(qty[i]),
                "price": float(rate[i]),
                "total": float(line_total[i]),
            },
        )

        # ==================================
        # REDUCE STOCK AGAIN
        # ==================================

        db.execute(
            text("""
                UPDATE products
                SET stock_qty =
                    stock_qty - :qty
                WHERE id=:product_id
            """),
            {"qty": float(qty[i]), "product_id": int(product_id[i])},
        )

    db.commit()
    db.close()

    return RedirectResponse(url="/sales", status_code=303)


@app.get("/sales/delete/{sale_id}")
def sales_delete(sale_id: int):

    db = SessionLocal()

    # ==================================
    # GET ITEMS
    # ==================================

    items = db.execute(
        text("""
            SELECT
                product_id,
                quantity
            FROM sale_items
            WHERE sale_id=:sale_id
        """),
        {"sale_id": sale_id},
    ).fetchall()

    # ==================================
    # RESTORE STOCK
    # ==================================

    for item in items:

        db.execute(
            text("""
                UPDATE products
                SET stock_qty =
                    stock_qty + :qty
                WHERE id=:product_id
            """),
            {"qty": item.quantity, "product_id": item.product_id},
        )

    # ==================================
    # DELETE ITEMS
    # ==================================

    db.execute(
        text("""
            DELETE FROM sale_items
            WHERE sale_id=:sale_id
        """),
        {"sale_id": sale_id},
    )

    # ==================================
    # DELETE HEADER
    # ==================================

    db.execute(
        text("""
            DELETE FROM sales
            WHERE id=:sale_id
        """),
        {"sale_id": sale_id},
    )

    db.commit()
    db.close()

    return RedirectResponse(url="/sales", status_code=303)


@app.get("/purchase-reports")
def purchase_reports(
    request: Request, from_date: str = None, to_date: str = None, supplier_id: int = 0
):

    db = SessionLocal()

    if not from_date:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    if not to_date:
        to_date = date.today().strftime("%Y-%m-%d")

    report = (
        db.execute(
            text("""
            SELECT

                p.purchase_id,
                p.purchase_no,
                p.purchase_date,
                s.supplier_name,
                p.invoice_no,

                COUNT(pi.purchase_item_id) AS total_items,

                IFNULL(SUM(pi.quantity),0) AS total_qty,

                IFNULL(SUM(pi.gst_amount),0) AS gst_amount,

                p.grand_total

            FROM purchase p

            LEFT JOIN suppliers s
                ON s.id = p.supplier_id

            LEFT JOIN purchase_items pi
                ON pi.purchase_id = p.purchase_id

            WHERE
                p.purchase_date BETWEEN :from_date AND :to_date
                AND (
                    :supplier_id = 0
                    OR p.supplier_id = :supplier_id
                )

            GROUP BY
                p.purchase_id,
                p.purchase_no,
                p.purchase_date,
                s.supplier_name,
                p.invoice_no,
                p.grand_total

            ORDER BY
                p.purchase_date DESC,
                p.purchase_id DESC
        """),
            {"from_date": from_date, "to_date": to_date, "supplier_id": supplier_id},
        )
        .mappings()
        .all()
    )

    summary = (
        db.execute(
            text("""
        SELECT

            COUNT(*) AS purchase_count,

            IFNULL(SUM(grand_total),0) AS purchase_amount

        FROM purchase p

        WHERE
            p.purchase_date BETWEEN :from_date AND :to_date
            AND (
                :supplier_id = 0
                OR p.supplier_id = :supplier_id
            )
    """),
            {"from_date": from_date, "to_date": to_date, "supplier_id": supplier_id},
        )
        .mappings()
        .first()
    )

    suppliers = db.execute(text("""
            SELECT
                id,
                supplier_name
            FROM suppliers
            ORDER BY supplier_name
        """)).mappings().all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="purchase_reports.html",
        context={
            "report": report,
            "suppliers": suppliers,
            "supplier_id": supplier_id,
            "purchase_count": summary["purchase_count"],
            "purchase_amount": summary["purchase_amount"],
            "from_date": from_date,
            "to_date": to_date,
        },
    )


@app.get("/sales-reports")
def sales_reports(
    request: Request, from_date: str = None, to_date: str = None, customer_id: int = 0
):

    db = SessionLocal()

    if not from_date:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    if not to_date:
        to_date = date.today().strftime("%Y-%m-%d")

    # ==========================
    # SALES REPORT
    # ==========================

    report = (
        db.execute(
            text("""
            SELECT

                s.id,
                s.invoice_number,
                s.sale_date,

                c.customer_name,

                COUNT(si.product_id) AS total_items,

                IFNULL(SUM(si.quantity),0) AS total_qty,

                IFNULL(s.gst_amount,0) AS gst_amount,

                s.grand_total

            FROM sales s

            LEFT JOIN customers c
                ON c.id = s.customer_id

            LEFT JOIN sale_items si
                ON si.sale_id = s.id

            WHERE
                s.sale_date BETWEEN :from_date AND :to_date

                AND (
                    :customer_id = 0
                    OR s.customer_id = :customer_id
                )

            GROUP BY

                s.id,
                s.invoice_number,
                s.sale_date,
                c.customer_name,
                s.gst_amount,
                s.grand_total

            ORDER BY

                s.sale_date DESC,
                s.id DESC

        """),
            {"from_date": from_date, "to_date": to_date, "customer_id": customer_id},
        )
        .mappings()
        .all()
    )

    # ==========================
    # SUMMARY
    # ==========================

    summary = (
        db.execute(
            text("""
        SELECT

            COUNT(*) AS sale_count,

            IFNULL(SUM(grand_total),0) AS sale_amount

        FROM sales s

        WHERE
            s.sale_date BETWEEN :from_date AND :to_date

            AND (
                :customer_id = 0
                OR s.customer_id = :customer_id
            )
    """),
            {"from_date": from_date, "to_date": to_date, "customer_id": customer_id},
        )
        .mappings()
        .first()
    )

    # ==========================
    # CUSTOMER LIST
    # ==========================

    customers = db.execute(text("""

            SELECT

                id,
                customer_name

            FROM customers

            ORDER BY customer_name

        """)).mappings().all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sales_reports.html",
        context={
            "report": report,
            "customers": customers,
            "customer_id": customer_id,
            "sale_count": summary["sale_count"],
            "sale_amount": summary["sale_amount"],
            "from_date": from_date,
            "to_date": to_date,
        },
    )


from datetime import date


@app.get("/monthly-purchase-report")
def monthly_purchase_report(
    request: Request,
    from_year: int = date.today().year,
    to_year: int = date.today().year,
    supplier_id: int = 0,
):

    db = SessionLocal()

    # ===============================
    # Supplier List
    # ===============================

    suppliers = db.execute(text("""
            SELECT
                id,
                supplier_name
            FROM suppliers
            ORDER BY supplier_name
        """)).mappings().all()

    # ===============================
    # Year List
    # ===============================

    years = list(range(date.today().year - 5, date.today().year + 1))

    # ===============================
    # Month Wise Purchase Report
    # ===============================

    report = (
        db.execute(
            text("""

            SELECT

                YEAR(p.purchase_date) AS year,

                MONTH(p.purchase_date) AS month_no,

                DATE_FORMAT(
                    p.purchase_date,
                    '%M - %Y'
                ) AS month_name,

                COUNT(DISTINCT p.purchase_id) AS purchase_count,

                IFNULL(SUM(pi.quantity),0) AS total_qty,

                IFNULL(SUM(pi.gst_amount),0) AS gst_amount,

                IFNULL(SUM(p.grand_total),0) AS purchase_amount

            FROM purchase p

            LEFT JOIN purchase_items pi
                ON pi.purchase_id = p.purchase_id

            WHERE

                YEAR(p.purchase_date)
                BETWEEN :from_year AND :to_year

                AND
                (
                    :supplier_id = 0
                    OR p.supplier_id = :supplier_id
                )

            GROUP BY

                YEAR(p.purchase_date),
                MONTH(p.purchase_date)

            ORDER BY

                YEAR(p.purchase_date),
                MONTH(p.purchase_date)

        """),
            {"from_year": from_year, "to_year": to_year, "supplier_id": supplier_id},
        )
        .mappings()
        .all()
    )

    # ===============================
    # Summary
    # ===============================

    summary = (
        db.execute(
            text("""

            SELECT

                COUNT(DISTINCT p.purchase_id)
                    AS purchase_count,

                IFNULL(SUM(pi.quantity),0)
                    AS total_qty,

                IFNULL(SUM(pi.gst_amount),0)
                    AS total_gst,

                IFNULL(SUM(p.grand_total),0)
                    AS purchase_amount

            FROM purchase p

            LEFT JOIN purchase_items pi
                ON pi.purchase_id = p.purchase_id

            WHERE

                YEAR(p.purchase_date)
                BETWEEN :from_year AND :to_year

                AND
                (
                    :supplier_id = 0
                    OR p.supplier_id = :supplier_id
                )

        """),
            {"from_year": from_year, "to_year": to_year, "supplier_id": supplier_id},
        )
        .mappings()
        .first()
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="monthly_purchase_report.html",
        context={
            "report": report,
            "years": years,
            "from_year": from_year,
            "to_year": to_year,
            "suppliers": suppliers,
            "supplier_id": supplier_id,
            "purchase_count": summary["purchase_count"],
            "purchase_amount": summary["purchase_amount"],
            "total_qty": summary["total_qty"],
            "total_gst": summary["total_gst"],
        },
    )


from datetime import date


@app.get("/monthly-sales-report")
def monthly_sales_report(
    request: Request,
    from_year: int = date.today().year,
    to_year: int = date.today().year,
    customer_id: int = 0,
):

    db = SessionLocal()

    # =====================================
    # Customer List
    # =====================================

    customers = db.execute(text("""
            SELECT
                id,
                customer_name
            FROM customers
            ORDER BY customer_name
        """)).mappings().all()

    # =====================================
    # Year List
    # =====================================

    years = list(range(date.today().year - 5, date.today().year + 1))

    # =====================================
    # Monthly Sales Report
    # =====================================

    report = (
        db.execute(
            text("""

        SELECT

            YEAR(x.sale_date) AS year,

            MONTH(x.sale_date) AS month_no,

            DATE_FORMAT(x.sale_date,'%M - %Y') AS month_name,

            COUNT(*) AS sale_count,

            SUM(x.total_qty) AS total_qty,

            SUM(x.gst_amount) AS gst_amount,

            SUM(x.grand_total) AS sale_amount

        FROM
        (

            SELECT

                s.id,

                s.sale_date,

                s.customer_id,

                s.gst_amount,

                s.grand_total,

                IFNULL(SUM(si.quantity),0) AS total_qty

            FROM sales s

            LEFT JOIN sale_items si
            ON si.sale_id = s.id

            WHERE

                YEAR(s.sale_date)
                BETWEEN :from_year AND :to_year

                AND
                (
                    :customer_id = 0
                    OR s.customer_id = :customer_id
                )

            GROUP BY

                s.id,
                s.sale_date,
                s.customer_id,
                s.gst_amount,
                s.grand_total

        ) x

        GROUP BY

            YEAR(x.sale_date),
            MONTH(x.sale_date)

        ORDER BY

            YEAR(x.sale_date),
            MONTH(x.sale_date)

    """),
            {"from_year": from_year, "to_year": to_year, "customer_id": customer_id},
        )
        .mappings()
        .all()
    )

    # =====================================
    # Summary
    # =====================================

    summary = (
        db.execute(
            text("""

        SELECT

            COUNT(*) AS sale_count,

            SUM(total_qty) AS total_qty,

            SUM(gst_amount) AS total_gst,

            SUM(grand_total) AS sale_amount

        FROM
        (

            SELECT

                s.id,

                s.gst_amount,

                s.grand_total,

                IFNULL(SUM(si.quantity),0) AS total_qty

            FROM sales s

            LEFT JOIN sale_items si
            ON si.sale_id = s.id

            WHERE

                YEAR(s.sale_date)
                BETWEEN :from_year AND :to_year

                AND
                (
                    :customer_id = 0
                    OR s.customer_id = :customer_id
                )

            GROUP BY

                s.id,
                s.gst_amount,
                s.grand_total

        ) x

    """),
            {"from_year": from_year, "to_year": to_year, "customer_id": customer_id},
        )
        .mappings()
        .first()
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="monthly_sales_report.html",
        context={
            "report": report,
            "customers": customers,
            "years": years,
            "from_year": from_year,
            "to_year": to_year,
            "customer_id": customer_id,
            "sale_count": summary["sale_count"],
            "sale_amount": summary["sale_amount"],
            "total_qty": summary["total_qty"],
            "total_gst": summary["total_gst"],
        },
    )


@app.get("/purchase-bank-statement")
def purchase_bank_statement(
    request: Request,
    month: int = 0,
    year: int = 0,
):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    db = SessionLocal()

    today = date.today()

    if not month:
        month = today.month

    if not year:
        year = today.year

    years = list(range(today.year - 5, today.year + 2))

    company = db.execute(text("""
        SELECT *
        FROM company
        LIMIT 1
    """)).mappings().first()

    report = db.execute(
        text("""
            SELECT
                p.purchase_date,
                s.supplier_name,
                s.gst_number,
                rm.material_name,
                pi.quantity,
                pi.unit_price,
                (pi.quantity * pi.unit_price) AS taxable_total,
                pi.gst_percent,
                pi.gst_amount,
                pi.line_total
            FROM purchase p
            LEFT JOIN suppliers s
                ON s.id = p.supplier_id
            LEFT JOIN purchase_items pi
                ON pi.purchase_id = p.purchase_id
            LEFT JOIN raw_materials rm
                ON rm.id = pi.material_id
            WHERE MONTH(p.purchase_date) = :month
            AND YEAR(p.purchase_date) = :year
            ORDER BY
                p.purchase_date,
                s.supplier_name,
                rm.material_name
        """),
        {"month": month, "year": year},
    ).mappings().all()

    summary = {
        "total_qty": sum(float(row.quantity or 0) for row in report),
        "total_taxable": sum(float(row.taxable_total or 0) for row in report),
        "total_gst": sum(float(row.gst_amount or 0) for row in report),
        "grand_total": sum(float(row.line_total or 0) for row in report),
    }

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="purchase_bank_statement.html",
        context={
            "request": request,
            "company": company,
            "report": report,
            "summary": summary,
            "month": month,
            "year": year,
            "years": years,
            "months": [
                {"id": 1, "name": "January"},
                {"id": 2, "name": "February"},
                {"id": 3, "name": "March"},
                {"id": 4, "name": "April"},
                {"id": 5, "name": "May"},
                {"id": 6, "name": "June"},
                {"id": 7, "name": "July"},
                {"id": 8, "name": "August"},
                {"id": 9, "name": "September"},
                {"id": 10, "name": "October"},
                {"id": 11, "name": "November"},
                {"id": 12, "name": "December"},
            ],
        },
    )


@app.get("/sales-bank-statement")
def sales_bank_statement(
    request: Request,
    month: int = 0,
    year: int = 0,
):

    db = SessionLocal()

    today = date.today()

    if not month:
        month = today.month

    if not year:
        year = today.year

    years = list(range(today.year - 5, today.year + 2))

    company = db.execute(text("""
        SELECT *
        FROM company
        LIMIT 1
    """)).mappings().first()

    report = db.execute(
        text("""
            SELECT
                s.sale_date,
                c.customer_name,
                c.gst_number,
                p.product_name,
                si.quantity,
                si.price,
                (si.quantity * si.price) AS taxable_total,
                IFNULL(p.gst_percent,0) AS gst_percent,
                ((si.quantity * si.price) * IFNULL(p.gst_percent,0) / 100) AS gst_amount,
                si.total AS line_total
            FROM sales s
            LEFT JOIN customers c
                ON c.id = s.customer_id
            LEFT JOIN sale_items si
                ON si.sale_id = s.id
            LEFT JOIN products p
                ON p.id = si.product_id
            WHERE MONTH(s.sale_date) = :month
            AND YEAR(s.sale_date) = :year
            ORDER BY
                s.sale_date,
                c.customer_name,
                p.product_name
        """),
        {"month": month, "year": year},
    ).mappings().all()

    summary = {
        "total_qty": sum(float(row.quantity or 0) for row in report),
        "total_taxable": sum(float(row.taxable_total or 0) for row in report),
        "total_gst": sum(float(row.gst_amount or 0) for row in report),
        "grand_total": sum(float(row.line_total or 0) for row in report),
    }

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sales_bank_statement.html",
        context={
            "request": request,
            "company": company,
            "report": report,
            "summary": summary,
            "month": month,
            "year": year,
            "years": years,
            "months": [
                {"id": 1, "name": "January"},
                {"id": 2, "name": "February"},
                {"id": 3, "name": "March"},
                {"id": 4, "name": "April"},
                {"id": 5, "name": "May"},
                {"id": 6, "name": "June"},
                {"id": 7, "name": "July"},
                {"id": 8, "name": "August"},
                {"id": 9, "name": "September"},
                {"id": 10, "name": "October"},
                {"id": 11, "name": "November"},
                {"id": 12, "name": "December"},
            ],
        },
    )


@app.get("/stock-valuation-report")
def stock_valuation_report(
    request: Request,
    item_type: str = "all",
    stock_status: str = "all",
):

    db = SessionLocal()

    raw_materials = (
        db.execute(
            text("""
                SELECT
                    id,
                    material_name AS item_name,
                    'raw' AS item_type,
                    'Raw Material' AS item_type_label,
                    unit,
                    stock_qty,
                    minimum_stock,
                    purchase_price AS cost_price,
                    NULL AS sale_price,
                    gst_percent
                FROM raw_materials
                ORDER BY material_name
            """)
        )
        .mappings()
        .all()
    )

    products = (
        db.execute(
            text("""
                SELECT
                    id,
                    product_name AS item_name,
                    'product' AS item_type,
                    'Finished Product' AS item_type_label,
                    category AS unit,
                    stock_qty,
                    0 AS minimum_stock,
                    purchase_price AS cost_price,
                    sale_price,
                    gst_percent
                FROM products
                ORDER BY product_name
            """)
        )
        .mappings()
        .all()
    )

    db.close()

    report = []

    for row in list(raw_materials) + list(products):

        item = dict(row)

        stock_qty = float(item.get("stock_qty") or 0)
        minimum_stock = float(item.get("minimum_stock") or 0)
        cost_price = float(item.get("cost_price") or 0)
        sale_price = float(item.get("sale_price") or 0)

        if stock_qty < 0:
            status = "negative"
            status_label = "Negative"
        elif stock_qty == 0:
            status = "zero"
            status_label = "No Stock"
        elif item["item_type"] == "raw" and stock_qty <= minimum_stock:
            status = "low"
            status_label = "Low Stock"
        else:
            status = "positive"
            status_label = "In Stock"

        item["stock_qty"] = stock_qty
        item["minimum_stock"] = minimum_stock
        item["cost_price"] = cost_price
        item["sale_price"] = sale_price
        item["cost_value"] = stock_qty * cost_price
        item["sale_value"] = stock_qty * sale_price if sale_price else 0
        item["status"] = status
        item["status_label"] = status_label

        if item_type != "all" and item["item_type"] != item_type:
            continue

        if stock_status != "all" and item["status"] != stock_status:
            continue

        report.append(item)

    total_items = len(report)
    total_qty = sum(item["stock_qty"] for item in report)
    total_cost_value = sum(item["cost_value"] for item in report)
    total_sale_value = sum(item["sale_value"] for item in report)
    low_stock_count = sum(1 for item in report if item["status"] in ("low", "negative", "zero"))
    raw_count = sum(1 for item in report if item["item_type"] == "raw")
    product_count = sum(1 for item in report if item["item_type"] == "product")

    return templates.TemplateResponse(
        request=request,
        name="stock_valuation_report.html",
        context={
            "request": request,
            "report": report,
            "item_type": item_type,
            "stock_status": stock_status,
            "total_items": total_items,
            "total_qty": total_qty,
            "total_cost_value": total_cost_value,
            "total_sale_value": total_sale_value,
            "low_stock_count": low_stock_count,
            "raw_count": raw_count,
            "product_count": product_count,
        },
    )


def ensure_supplier_payments_table(db):
    return None


@app.get("/supplier-outstanding-report")
def supplier_outstanding_report(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    supplier_id: int = 0,
    status: str = "all",
):

    db = SessionLocal()
    ensure_supplier_payments_table(db)

    suppliers = db.execute(text("""
        SELECT
            id,
            supplier_name,
            company_name
        FROM suppliers
        ORDER BY supplier_name
    """)).mappings().all()

    params = {
        "from_date": from_date,
        "to_date": to_date,
        "supplier_id": supplier_id,
    }

    report = db.execute(
        text("""
            SELECT
                s.id,
                s.supplier_name,
                s.company_name,
                s.mobile,
                IFNULL(p.purchase_count,0) AS purchase_count,
                IFNULL(p.purchase_amount,0) AS purchase_amount,
                IFNULL(pay.payment_count,0) AS payment_count,
                IFNULL(pay.paid_amount,0) AS paid_amount,
                IFNULL(p.purchase_amount,0) - IFNULL(pay.paid_amount,0) AS balance_amount,
                pay.last_payment_date
            FROM suppliers s
            LEFT JOIN
            (
                SELECT
                    supplier_id,
                    COUNT(*) AS purchase_count,
                    SUM(grand_total) AS purchase_amount
                FROM purchase
                WHERE (:from_date = '' OR purchase_date >= :from_date)
                AND (:to_date = '' OR purchase_date <= :to_date)
                GROUP BY supplier_id
            ) p
                ON p.supplier_id = s.id
            LEFT JOIN
            (
                SELECT
                    supplier_id,
                    COUNT(*) AS payment_count,
                    SUM(amount) AS paid_amount,
                    MAX(payment_date) AS last_payment_date
                FROM supplier_payments
                WHERE (:from_date = '' OR payment_date >= :from_date)
                AND (:to_date = '' OR payment_date <= :to_date)
                GROUP BY supplier_id
            ) pay
                ON pay.supplier_id = s.id
            WHERE (:supplier_id = 0 OR s.id = :supplier_id)
            ORDER BY balance_amount DESC, s.supplier_name
        """),
        params,
    ).mappings().all()

    filtered_report = []

    for row in report:
        item = dict(row)
        balance = float(item["balance_amount"] or 0)

        if balance > 0:
            item["status"] = "due"
            item["status_label"] = "Payment Due"
        elif balance < 0:
            item["status"] = "advance"
            item["status_label"] = "Advance Paid"
        else:
            item["status"] = "clear"
            item["status_label"] = "Settled"

        if status != "all" and item["status"] != status:
            continue

        filtered_report.append(item)

    payments = db.execute(
        text("""
            SELECT
                sp.id,
                sp.supplier_id,
                sp.payment_date,
                sp.amount,
                sp.payment_mode,
                sp.reference_no,
                sp.notes,
                s.supplier_name
            FROM supplier_payments sp
            LEFT JOIN suppliers s
                ON s.id = sp.supplier_id
            WHERE (:supplier_id = 0 OR sp.supplier_id = :supplier_id)
            AND (:from_date = '' OR sp.payment_date >= :from_date)
            AND (:to_date = '' OR sp.payment_date <= :to_date)
            ORDER BY sp.payment_date DESC, sp.id DESC
            LIMIT 50
        """),
        params,
    ).mappings().all()

    total_purchase_amount = sum(float(item["purchase_amount"] or 0) for item in filtered_report)
    total_paid_amount = sum(float(item["paid_amount"] or 0) for item in filtered_report)
    total_balance_amount = sum(float(item["balance_amount"] or 0) for item in filtered_report)
    due_supplier_count = sum(1 for item in filtered_report if item["status"] == "due")

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="supplier_outstanding_report.html",
        context={
            "request": request,
            "suppliers": suppliers,
            "report": filtered_report,
            "payments": payments,
            "from_date": from_date,
            "to_date": to_date,
            "supplier_id": supplier_id,
            "status": status,
            "today": date.today().strftime("%Y-%m-%d"),
            "total_purchase_amount": total_purchase_amount,
            "total_paid_amount": total_paid_amount,
            "total_balance_amount": total_balance_amount,
            "due_supplier_count": due_supplier_count,
        },
    )


@app.post("/supplier-payment/save")
def supplier_payment_save(
    supplier_id: int = Form(...),
    payment_date: str = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    notes: str = Form(""),
):

    db = SessionLocal()
    ensure_supplier_payments_table(db)

    db.execute(
        text("""
            INSERT INTO supplier_payments
            (
                supplier_id,
                payment_date,
                amount,
                payment_mode,
                reference_no,
                notes
            )
            VALUES
            (
                :supplier_id,
                :payment_date,
                :amount,
                :payment_mode,
                :reference_no,
                :notes
            )
        """),
        {
            "supplier_id": supplier_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "notes": notes,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/supplier-outstanding-report", status_code=303)


@app.post("/supplier-payment/update")
def supplier_payment_update(
    payment_id: int = Form(...),
    supplier_id: int = Form(...),
    payment_date: str = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    notes: str = Form(""),
):

    db = SessionLocal()
    ensure_supplier_payments_table(db)

    db.execute(
        text("""
            UPDATE supplier_payments
            SET
                supplier_id=:supplier_id,
                payment_date=:payment_date,
                amount=:amount,
                payment_mode=:payment_mode,
                reference_no=:reference_no,
                notes=:notes
            WHERE id=:payment_id
        """),
        {
            "payment_id": payment_id,
            "supplier_id": supplier_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "notes": notes,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/supplier-outstanding-report", status_code=303)


@app.get("/customer-outstanding-report")
def customer_outstanding_report(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    customer_id: int = 0,
    status: str = "all",
):

    db = SessionLocal()

    customers = db.execute(text("""
        SELECT
            id,
            customer_name,
            company_name
        FROM customers
        ORDER BY customer_name
    """)).mappings().all()

    params = {
        "from_date": from_date,
        "to_date": to_date,
        "customer_id": customer_id,
    }

    report = db.execute(
        text("""
            SELECT
                c.id,
                c.customer_name,
                c.company_name,
                c.mobile,
                IFNULL(s.sale_count,0) AS sale_count,
                IFNULL(s.sale_amount,0) AS sale_amount,
                IFNULL(pay.payment_count,0) AS payment_count,
                IFNULL(pay.received_amount,0) AS received_amount,
                IFNULL(s.sale_amount,0) - IFNULL(pay.received_amount,0) AS balance_amount,
                pay.last_payment_date
            FROM customers c
            LEFT JOIN
            (
                SELECT
                    customer_id,
                    COUNT(*) AS sale_count,
                    SUM(grand_total) AS sale_amount
                FROM sales
                WHERE (:from_date = '' OR sale_date >= :from_date)
                AND (:to_date = '' OR sale_date <= :to_date)
                GROUP BY customer_id
            ) s
                ON s.customer_id = c.id
            LEFT JOIN
            (
                SELECT
                    customer_id,
                    COUNT(*) AS payment_count,
                    SUM(amount) AS received_amount,
                    MAX(payment_date) AS last_payment_date
                FROM customer_payments
                WHERE (:from_date = '' OR payment_date >= :from_date)
                AND (:to_date = '' OR payment_date <= :to_date)
                GROUP BY customer_id
            ) pay
                ON pay.customer_id = c.id
            WHERE (:customer_id = 0 OR c.id = :customer_id)
            ORDER BY balance_amount DESC, c.customer_name
        """),
        params,
    ).mappings().all()

    filtered_report = []

    for row in report:
        item = dict(row)
        balance = float(item["balance_amount"] or 0)

        if balance > 0:
            item["status"] = "due"
            item["status_label"] = "Collection Due"
        elif balance < 0:
            item["status"] = "advance"
            item["status_label"] = "Advance Received"
        else:
            item["status"] = "clear"
            item["status_label"] = "Settled"

        if status != "all" and item["status"] != status:
            continue

        filtered_report.append(item)

    payments = db.execute(
        text("""
            SELECT
                cp.id,
                cp.customer_id,
                cp.payment_date,
                cp.amount,
                cp.payment_mode,
                cp.reference_no,
                cp.notes,
                c.customer_name
            FROM customer_payments cp
            LEFT JOIN customers c
                ON c.id = cp.customer_id
            WHERE (:customer_id = 0 OR cp.customer_id = :customer_id)
            AND (:from_date = '' OR cp.payment_date >= :from_date)
            AND (:to_date = '' OR cp.payment_date <= :to_date)
            ORDER BY cp.payment_date DESC, cp.id DESC
            LIMIT 50
        """),
        params,
    ).mappings().all()

    total_sale_amount = sum(float(item["sale_amount"] or 0) for item in filtered_report)
    total_received_amount = sum(float(item["received_amount"] or 0) for item in filtered_report)
    total_balance_amount = sum(float(item["balance_amount"] or 0) for item in filtered_report)
    due_customer_count = sum(1 for item in filtered_report if item["status"] == "due")

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="customer_outstanding_report.html",
        context={
            "request": request,
            "customers": customers,
            "report": filtered_report,
            "payments": payments,
            "from_date": from_date,
            "to_date": to_date,
            "customer_id": customer_id,
            "status": status,
            "today": date.today().strftime("%Y-%m-%d"),
            "total_sale_amount": total_sale_amount,
            "total_received_amount": total_received_amount,
            "total_balance_amount": total_balance_amount,
            "due_customer_count": due_customer_count,
        },
    )


@app.post("/customer-payment/save")
def customer_payment_save(
    customer_id: int = Form(...),
    payment_date: str = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    notes: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO customer_payments
            (
                customer_id,
                payment_date,
                amount,
                payment_mode,
                reference_no,
                notes
            )
            VALUES
            (
                :customer_id,
                :payment_date,
                :amount,
                :payment_mode,
                :reference_no,
                :notes
            )
        """),
        {
            "customer_id": customer_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "notes": notes,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/customer-outstanding-report", status_code=303)


@app.post("/customer-payment/update")
def customer_payment_update(
    payment_id: int = Form(...),
    customer_id: int = Form(...),
    payment_date: str = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    notes: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE customer_payments
            SET
                customer_id=:customer_id,
                payment_date=:payment_date,
                amount=:amount,
                payment_mode=:payment_mode,
                reference_no=:reference_no,
                notes=:notes
            WHERE id=:payment_id
        """),
        {
            "payment_id": payment_id,
            "customer_id": customer_id,
            "payment_date": payment_date,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "notes": notes,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/customer-outstanding-report", status_code=303)


def get_account_month_defaults(from_date: str = "", to_date: str = ""):
    today = date.today()

    if not from_date:
        from_date = today.replace(day=1).strftime("%Y-%m-%d")

    if not to_date:
        to_date = today.strftime("%Y-%m-%d")

    return from_date, to_date


def table_exists(db, table_name: str):
    return db.execute(
        text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
        """),
        {"table_name": table_name},
    ).scalar() > 0


def get_expense_categories(db, include_inactive: bool = False):
    status_filter = "" if include_inactive else "AND status='Active'"
    return db.execute(text(f"""
        SELECT id, account_name, status
        FROM account_heads
        WHERE account_type='Expense'
        {status_filter}
        ORDER BY account_name
    """)).mappings().all()


@app.get("/expenses")
def expenses_page(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    category_id: int = 0,
):
    from_date, to_date = get_account_month_defaults(from_date, to_date)
    today = date.today()
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    today_value = today.strftime("%Y-%m-%d")
    db = SessionLocal()

    categories = get_expense_categories(db, include_inactive=True)
    active_categories = [row for row in categories if row.status == "Active"]
    expenses = db.execute(text("""
        SELECT atx.*, ah.account_name AS category_name
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE ah.account_type='Expense'
          AND atx.transaction_date BETWEEN :from_date AND :to_date
          AND (:category_id=0 OR atx.account_id=:category_id)
        ORDER BY atx.transaction_date DESC, atx.id DESC
    """), {
        "from_date": from_date,
        "to_date": to_date,
        "category_id": category_id,
    }).mappings().all()

    period_total = sum(float(row.amount or 0) for row in expenses)
    today_total = db.execute(text("""
        SELECT COALESCE(SUM(atx.amount), 0)
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE ah.account_type='Expense'
          AND atx.transaction_date=:today
    """), {"today": today_value}).scalar() or 0
    month_total = db.execute(text("""
        SELECT COALESCE(SUM(atx.amount), 0)
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE ah.account_type='Expense'
          AND atx.transaction_date BETWEEN :month_start AND :today
    """), {"month_start": month_start, "today": today_value}).scalar() or 0
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="expenses.html",
        context={
            "request": request,
            "categories": categories,
            "active_categories": active_categories,
            "expenses": expenses,
            "from_date": from_date,
            "to_date": to_date,
            "category_id": category_id,
            "today": today_value,
            "today_total": float(today_total),
            "month_total": float(month_total),
            "period_total": period_total,
        },
    )


@app.post("/expense/save")
def expense_save(
    transaction_date: str = Form(...),
    category_id: int = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    narration: str = Form(""),
):
    if amount <= 0:
        return RedirectResponse("/expenses", status_code=303)
    db = SessionLocal()
    db.execute(text("""
        INSERT INTO account_transactions
            (transaction_date, account_id, amount, payment_mode, reference_no, narration)
        SELECT :transaction_date, id, :amount, :payment_mode, :reference_no, :narration
        FROM account_heads
        WHERE id=:category_id AND account_type='Expense' AND status='Active'
    """), {
        "transaction_date": transaction_date,
        "category_id": category_id,
        "amount": amount,
        "payment_mode": payment_mode,
        "reference_no": reference_no.strip(),
        "narration": narration.strip(),
    })
    db.commit()
    db.close()
    return RedirectResponse("/expenses", status_code=303)


@app.post("/expense/update")
def expense_update(
    expense_id: int = Form(...),
    transaction_date: str = Form(...),
    category_id: int = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    narration: str = Form(""),
):
    if amount <= 0:
        return RedirectResponse("/expenses", status_code=303)
    db = SessionLocal()
    db.execute(text("""
        UPDATE account_transactions
        SET transaction_date=:transaction_date,
            account_id=:category_id,
            amount=:amount,
            payment_mode=:payment_mode,
            reference_no=:reference_no,
            narration=:narration
        WHERE id=:expense_id
          AND account_id IN (
              SELECT id FROM account_heads WHERE account_type='Expense'
          )
          AND :category_id IN (
              SELECT id FROM account_heads WHERE account_type='Expense' AND status='Active'
          )
    """), {
        "expense_id": expense_id,
        "transaction_date": transaction_date,
        "category_id": category_id,
        "amount": amount,
        "payment_mode": payment_mode,
        "reference_no": reference_no.strip(),
        "narration": narration.strip(),
    })
    db.commit()
    db.close()
    return RedirectResponse("/expenses", status_code=303)


@app.post("/expense/delete/{expense_id}")
def expense_delete(expense_id: int):
    db = SessionLocal()
    db.execute(text("""
        DELETE FROM account_transactions
        WHERE id=:expense_id
          AND account_id IN (
              SELECT id FROM account_heads WHERE account_type='Expense'
          )
    """), {"expense_id": expense_id})
    db.commit()
    db.close()
    return RedirectResponse("/expenses", status_code=303)


@app.get("/expense-reports")
def expense_reports(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    category_id: int = 0,
    group_by: str = "day",
):
    from_date, to_date = get_account_month_defaults(from_date, to_date)
    group_by = "month" if group_by == "month" else "day"
    period_expression = (
        "DATE_FORMAT(atx.transaction_date, '%Y-%m')"
        if group_by == "month"
        else "DATE_FORMAT(atx.transaction_date, '%Y-%m-%d')"
    )
    db = SessionLocal()
    categories = get_expense_categories(db, include_inactive=True)
    rows = db.execute(text(f"""
        SELECT {period_expression} AS period_label,
               COUNT(*) AS entry_count,
               SUM(atx.amount) AS total_amount
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE ah.account_type='Expense'
          AND atx.transaction_date BETWEEN :from_date AND :to_date
          AND (:category_id=0 OR atx.account_id=:category_id)
        GROUP BY {period_expression}
        ORDER BY period_label DESC
    """), {
        "from_date": from_date,
        "to_date": to_date,
        "category_id": category_id,
    }).mappings().all()
    category_rows = db.execute(text("""
        SELECT ah.account_name AS category_name,
               COUNT(*) AS entry_count,
               SUM(atx.amount) AS total_amount
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE ah.account_type='Expense'
          AND atx.transaction_date BETWEEN :from_date AND :to_date
          AND (:category_id=0 OR atx.account_id=:category_id)
        GROUP BY ah.id, ah.account_name
        ORDER BY total_amount DESC
    """), {
        "from_date": from_date,
        "to_date": to_date,
        "category_id": category_id,
    }).mappings().all()
    total_amount = sum(float(row.total_amount or 0) for row in rows)
    total_entries = sum(int(row.entry_count or 0) for row in rows)
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="expense_reports.html",
        context={
            "request": request,
            "categories": categories,
            "rows": rows,
            "category_rows": category_rows,
            "from_date": from_date,
            "to_date": to_date,
            "category_id": category_id,
            "group_by": group_by,
            "total_amount": total_amount,
            "total_entries": total_entries,
        },
    )


@app.get("/accounts")
def accounts_dashboard(request: Request):
    today = date.today()
    from_date = today.replace(day=1).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    db = SessionLocal()

    summary = db.execute(text("""
        SELECT
            COALESCE(SUM(CASE WHEN ah.account_type='Income' THEN atx.amount ELSE 0 END), 0) AS income_total,
            COALESCE(SUM(CASE WHEN ah.account_type='Expense' THEN atx.amount ELSE 0 END), 0) AS expense_total,
            COUNT(atx.id) AS transaction_count
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        WHERE atx.transaction_date BETWEEN :from_date AND :to_date
    """), {"from_date": from_date, "to_date": to_date}).mappings().first()

    recent_transactions = db.execute(text("""
        SELECT atx.transaction_date, atx.amount, atx.payment_mode,
               atx.narration, ah.account_name, ah.account_type
        FROM account_transactions atx
        JOIN account_heads ah ON ah.id=atx.account_id
        ORDER BY atx.transaction_date DESC, atx.id DESC
        LIMIT 6
    """)).mappings().all()
    db.close()

    income_total = float(summary.income_total or 0)
    expense_total = float(summary.expense_total or 0)
    return templates.TemplateResponse(
        request=request,
        name="accounts_dashboard.html",
        context={
            "request": request,
            "income_total": income_total,
            "expense_total": expense_total,
            "net_total": income_total - expense_total,
            "transaction_count": int(summary.transaction_count or 0),
            "recent_transactions": recent_transactions,
            "month_label": today.strftime("%B %Y"),
        },
    )


@app.get("/income-expenses")
def accounts_page(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    account_type: str = "all",
    account_id: int = 0,
):

    from_date, to_date = get_account_month_defaults(from_date, to_date)

    db = SessionLocal()

    heads = db.execute(text("""
        SELECT *
        FROM account_heads
        WHERE status='Active'
        ORDER BY account_type, account_name
    """)).mappings().all()

    transactions = db.execute(
        text("""
            SELECT
                atx.*,
                ah.account_name,
                ah.account_type
            FROM account_transactions atx
            LEFT JOIN account_heads ah
                ON ah.id = atx.account_id
            WHERE atx.transaction_date BETWEEN :from_date AND :to_date
            AND (:account_type = 'all' OR ah.account_type = :account_type)
            AND (:account_id = 0 OR atx.account_id = :account_id)
            ORDER BY atx.transaction_date DESC, atx.id DESC
        """),
        {
            "from_date": from_date,
            "to_date": to_date,
            "account_type": account_type,
            "account_id": account_id,
        },
    ).mappings().all()

    income_total = sum(float(row.amount or 0) for row in transactions if row.account_type == "Income")
    expense_total = sum(float(row.amount or 0) for row in transactions if row.account_type == "Expense")
    net_total = income_total - expense_total

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="accounts.html",
        context={
            "request": request,
            "heads": heads,
            "transactions": transactions,
            "from_date": from_date,
            "to_date": to_date,
            "account_type": account_type,
            "account_id": account_id,
            "today": date.today().strftime("%Y-%m-%d"),
            "income_total": income_total,
            "expense_total": expense_total,
            "net_total": net_total,
        },
    )


@app.post("/account-head/save")
def account_head_save(
    account_name: str = Form(...),
    account_type: str = Form(...),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO account_heads
            (
                account_name,
                account_type,
                status
            )
            VALUES
            (
                :account_name,
                :account_type,
                'Active'
            )
        """),
        {
            "account_name": account_name,
            "account_type": account_type,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/income-expenses", status_code=303)


@app.post("/account-transaction/save")
def account_transaction_save(
    transaction_date: str = Form(...),
    account_id: int = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    narration: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO account_transactions
            (
                transaction_date,
                account_id,
                amount,
                payment_mode,
                reference_no,
                narration
            )
            VALUES
            (
                :transaction_date,
                :account_id,
                :amount,
                :payment_mode,
                :reference_no,
                :narration
            )
        """),
        {
            "transaction_date": transaction_date,
            "account_id": account_id,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "narration": narration,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/income-expenses", status_code=303)


@app.post("/account-transaction/update")
def account_transaction_update(
    transaction_id: int = Form(...),
    transaction_date: str = Form(...),
    account_id: int = Form(...),
    amount: float = Form(...),
    payment_mode: str = Form("Cash"),
    reference_no: str = Form(""),
    narration: str = Form(""),
):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE account_transactions
            SET
                transaction_date=:transaction_date,
                account_id=:account_id,
                amount=:amount,
                payment_mode=:payment_mode,
                reference_no=:reference_no,
                narration=:narration
            WHERE id=:transaction_id
        """),
        {
            "transaction_id": transaction_id,
            "transaction_date": transaction_date,
            "account_id": account_id,
            "amount": amount,
            "payment_mode": payment_mode,
            "reference_no": reference_no,
            "narration": narration,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/income-expenses", status_code=303)


@app.get("/account-transaction/delete/{transaction_id}")
def account_transaction_delete(transaction_id: int):

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM account_transactions
            WHERE id=:transaction_id
        """),
        {"transaction_id": transaction_id},
    )

    db.commit()
    db.close()

    return RedirectResponse("/income-expenses", status_code=303)


@app.get("/accounts-ledger")
def accounts_ledger(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    account_type: str = "all",
    account_id: int = 0,
):

    from_date, to_date = get_account_month_defaults(from_date, to_date)

    db = SessionLocal()

    heads = db.execute(text("""
        SELECT *
        FROM account_heads
        WHERE status='Active'
        ORDER BY account_type, account_name
    """)).mappings().all()

    ledger = db.execute(
        text("""
            SELECT
                atx.transaction_date,
                ah.account_name,
                ah.account_type,
                atx.payment_mode,
                atx.reference_no,
                atx.narration,
                CASE WHEN ah.account_type = 'Income' THEN atx.amount ELSE 0 END AS income_amount,
                CASE WHEN ah.account_type = 'Expense' THEN atx.amount ELSE 0 END AS expense_amount
            FROM account_transactions atx
            LEFT JOIN account_heads ah
                ON ah.id = atx.account_id
            WHERE atx.transaction_date BETWEEN :from_date AND :to_date
            AND (:account_type = 'all' OR ah.account_type = :account_type)
            AND (:account_id = 0 OR atx.account_id = :account_id)
            ORDER BY atx.transaction_date, atx.id
        """),
        {
            "from_date": from_date,
            "to_date": to_date,
            "account_type": account_type,
            "account_id": account_id,
        },
    ).mappings().all()

    company = db.execute(text("SELECT * FROM company LIMIT 1")).mappings().first()

    total_income = sum(float(row.income_amount or 0) for row in ledger)
    total_expense = sum(float(row.expense_amount or 0) for row in ledger)
    net_total = total_income - total_expense

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="accounts_ledger.html",
        context={
            "request": request,
            "company": company,
            "heads": heads,
            "ledger": ledger,
            "from_date": from_date,
            "to_date": to_date,
            "account_type": account_type,
            "account_id": account_id,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_total": net_total,
        },
    )


@app.get("/ai-expense-analyzer")
def ai_expense_analyzer(
    request: Request,
    from_date: str = "",
    to_date: str = "",
):

    from_date, to_date = get_account_month_defaults(from_date, to_date)

    db = SessionLocal()

    has_accounts = table_exists(db, "account_heads") and table_exists(db, "account_transactions")

    expense_rows = []
    mode_rows = []
    total_income = 0
    total_expense = 0
    net_total = 0
    insights = []

    if has_accounts:
        expense_rows = db.execute(
            text("""
                SELECT
                    ah.account_name,
                    SUM(atx.amount) AS total_amount,
                    COUNT(*) AS entry_count
                FROM account_transactions atx
                LEFT JOIN account_heads ah
                    ON ah.id = atx.account_id
                WHERE atx.transaction_date BETWEEN :from_date AND :to_date
                AND ah.account_type = 'Expense'
                GROUP BY ah.account_name
                ORDER BY total_amount DESC
            """),
            {"from_date": from_date, "to_date": to_date},
        ).mappings().all()

        mode_rows = db.execute(
            text("""
                SELECT
                    payment_mode,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS entry_count
                FROM account_transactions atx
                LEFT JOIN account_heads ah
                    ON ah.id = atx.account_id
                WHERE atx.transaction_date BETWEEN :from_date AND :to_date
                AND ah.account_type = 'Expense'
                GROUP BY payment_mode
                ORDER BY total_amount DESC
            """),
            {"from_date": from_date, "to_date": to_date},
        ).mappings().all()

        summary = db.execute(
            text("""
                SELECT
                    IFNULL(SUM(CASE WHEN ah.account_type = 'Income' THEN atx.amount ELSE 0 END),0) AS income_total,
                    IFNULL(SUM(CASE WHEN ah.account_type = 'Expense' THEN atx.amount ELSE 0 END),0) AS expense_total
                FROM account_transactions atx
                LEFT JOIN account_heads ah
                    ON ah.id = atx.account_id
                WHERE atx.transaction_date BETWEEN :from_date AND :to_date
            """),
            {"from_date": from_date, "to_date": to_date},
        ).mappings().first()

        total_income = float(summary["income_total"] or 0)
        total_expense = float(summary["expense_total"] or 0)
        net_total = total_income - total_expense

        if total_expense > total_income and total_income > 0:
            insights.append({
                "type": "risk",
                "title": "Expense is higher than income",
                "message": "This period has negative cash flow. Review non-essential expense heads first."
            })
        elif net_total > 0:
            insights.append({
                "type": "good",
                "title": "Income is covering expenses",
                "message": "This period is positive. Keep checking large expense heads for control."
            })

        if expense_rows:
            top = expense_rows[0]
            top_amount = float(top["total_amount"] or 0)
            share = (top_amount / total_expense * 100) if total_expense else 0
            insights.append({
                "type": "focus",
                "title": f"Highest expense: {top['account_name']}",
                "message": f"This head uses {share:.1f}% of total expenses. Verify if it is expected."
            })

            if share >= 40:
                insights.append({
                    "type": "risk",
                    "title": "Expense concentration detected",
                    "message": "One expense head is consuming a large share. Consider splitting or reviewing this cost."
                })

        if mode_rows:
            cash_row = next((row for row in mode_rows if (row["payment_mode"] or "").lower() == "cash"), None)
            if cash_row and total_expense:
                cash_share = float(cash_row["total_amount"] or 0) / total_expense * 100
                if cash_share >= 60:
                    insights.append({
                        "type": "focus",
                        "title": "High cash expense usage",
                        "message": f"Cash expenses are {cash_share:.1f}% of total expense. Bank/UPI records may be easier to reconcile."
                    })

        if not insights:
            insights.append({
                "type": "focus",
                "title": "Not enough expense movement yet",
                "message": "Add more income and expense entries to generate stronger insights."
            })

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="ai_expense_analyzer.html",
        context={
            "request": request,
            "has_accounts": has_accounts,
            "from_date": from_date,
            "to_date": to_date,
            "expense_rows": expense_rows,
            "mode_rows": mode_rows,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_total": net_total,
            "insights": insights,
        },
    )


@app.get("/ai-chatbot")
def ai_chatbot(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="ai_chatbot.html",
        context={"request": request},
    )


@app.post("/ai-chatbot/ask")
async def ai_chatbot_ask(request: Request):

    data = await request.json()
    question = (data.get("question") or "").strip()
    query = question.lower()

    db = SessionLocal()

    answer = "I can answer about sales, purchase, customer outstanding, supplier outstanding, expenses, income, ledger, salary, and reports. Try asking: What is today's sales?"
    suggestions = [
        "What is today's sales?",
        "What is this month purchase?",
        "Show customer outstanding",
        "Analyze expenses",
    ]

    if "today" in query and "sale" in query:
        value = db.execute(text("""
            SELECT IFNULL(SUM(grand_total),0)
            FROM sales
            WHERE sale_date = CURDATE()
        """)).scalar()
        answer = f"Today's sales total is Rs. {float(value or 0):,.2f}."

    elif "month" in query and "sale" in query:
        value = db.execute(text("""
            SELECT IFNULL(SUM(grand_total),0)
            FROM sales
            WHERE MONTH(sale_date)=MONTH(CURDATE())
            AND YEAR(sale_date)=YEAR(CURDATE())
        """)).scalar()
        answer = f"This month sales total is Rs. {float(value or 0):,.2f}."

    elif "today" in query and "purchase" in query:
        value = db.execute(text("""
            SELECT IFNULL(SUM(grand_total),0)
            FROM purchase
            WHERE purchase_date = CURDATE()
        """)).scalar()
        answer = f"Today's purchase total is Rs. {float(value or 0):,.2f}."

    elif "month" in query and "purchase" in query:
        value = db.execute(text("""
            SELECT IFNULL(SUM(grand_total),0)
            FROM purchase
            WHERE MONTH(purchase_date)=MONTH(CURDATE())
            AND YEAR(purchase_date)=YEAR(CURDATE())
        """)).scalar()
        answer = f"This month purchase total is Rs. {float(value or 0):,.2f}."

    elif "customer" in query and ("outstanding" in query or "due" in query or "pending" in query):
        has_payments = table_exists(db, "customer_payments")
        if has_payments:
            value = db.execute(text("""
                SELECT IFNULL(s.sale_amount,0) - IFNULL(paid.received_amount,0)
                FROM
                (
                    SELECT IFNULL(SUM(grand_total),0) AS sale_amount
                    FROM sales
                ) s
                CROSS JOIN
                (
                    SELECT IFNULL(SUM(amount),0) AS received_amount
                    FROM customer_payments
                ) paid
            """)).scalar()
            answer = f"Customer outstanding is Rs. {float(value or 0):,.2f}. Open Customer Outstanding report for party-wise details."
        else:
            answer = "Customer payment table is not created yet. Run the customer_payments SQL first."

    elif "supplier" in query and ("outstanding" in query or "due" in query or "pending" in query):
        has_payments = table_exists(db, "supplier_payments")
        if has_payments:
            value = db.execute(text("""
                SELECT IFNULL(p.purchase_amount,0) - IFNULL(paid.paid_amount,0)
                FROM
                (
                    SELECT IFNULL(SUM(grand_total),0) AS purchase_amount
                    FROM purchase
                ) p
                CROSS JOIN
                (
                    SELECT IFNULL(SUM(amount),0) AS paid_amount
                    FROM supplier_payments
                ) paid
            """)).scalar()
            answer = f"Supplier outstanding is Rs. {float(value or 0):,.2f}. Open Supplier Outstanding report for supplier-wise details."
        else:
            answer = "Supplier payment table is not created yet. Run the supplier_payments SQL first."

    elif "expense" in query or "income" in query or "ledger" in query:
        has_accounts = table_exists(db, "account_heads") and table_exists(db, "account_transactions")
        if has_accounts:
            row = db.execute(text("""
                SELECT
                    IFNULL(SUM(CASE WHEN ah.account_type='Income' THEN atx.amount ELSE 0 END),0) AS income_total,
                    IFNULL(SUM(CASE WHEN ah.account_type='Expense' THEN atx.amount ELSE 0 END),0) AS expense_total
                FROM account_transactions atx
                LEFT JOIN account_heads ah
                    ON ah.id = atx.account_id
                WHERE MONTH(atx.transaction_date)=MONTH(CURDATE())
                AND YEAR(atx.transaction_date)=YEAR(CURDATE())
            """)).mappings().first()
            income = float(row["income_total"] or 0)
            expense = float(row["expense_total"] or 0)
            answer = f"This month income is Rs. {income:,.2f}, expense is Rs. {expense:,.2f}, and net balance is Rs. {income - expense:,.2f}."
        else:
            answer = "Accounts tables are not created yet. Run account_heads and account_transactions SQL first."

    elif "salary" in query or "attendance" in query:
        has_employees = table_exists(db, "employees")
        if has_employees:
            count = db.execute(text("SELECT COUNT(*) FROM employees WHERE status='Active'")).scalar()
            answer = f"There are {int(count or 0)} active employees. Use Attendance and Salary Receipt screens for payroll."
        else:
            answer = "Employee tables are not created yet. Run employee SQL first."

    elif "report" in query:
        answer = "Important reports available: Purchase Report, Sales Report, Monthly Sales, Monthly Purchase, Stock Valuation, Supplier Outstanding, Customer Outstanding, Accounts Ledger, Purchase Bank Statement, and Sales Bank Statement."

    db.close()

    return JSONResponse({
        "answer": answer,
        "suggestions": suggestions,
    })


@app.get("/users")
def users_page(request: Request):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    db = SessionLocal()

    users = db.execute(text("""
        SELECT *
        FROM users
        ORDER BY username
    """)).mappings().all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"request": request, "users": users},
    )


@app.get("/user/add")
def user_add(request: Request):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    return templates.TemplateResponse(
        request=request,
        name="user_form.html",
        context={"request": request, "user": None},
    )


@app.post("/user/save")
def user_save(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    role: str = Form("User"),
    status: str = Form("Active"),
):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO users
            (
                username,
                password,
                full_name,
                role,
                status
            )
            VALUES
            (
                :username,
                :password,
                :full_name,
                :role,
                :status
            )
        """),
        {
            "username": username,
            "password": password,
            "full_name": full_name,
            "role": role,
            "status": status,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/users", status_code=303)


@app.get("/user/edit/{user_id}")
def user_edit(user_id: int, request: Request):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    db = SessionLocal()

    user = db.execute(
        text("""
            SELECT *
            FROM users
            WHERE id=:user_id
        """),
        {"user_id": user_id},
    ).mappings().first()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="user_form.html",
        context={"request": request, "user": user},
    )


@app.post("/user/update")
def user_update(
    request: Request,
    user_id: int = Form(...),
    username: str = Form(...),
    password: str = Form(""),
    full_name: str = Form(""),
    role: str = Form("User"),
    status: str = Form("Active"),
):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    password_sql = ", password=:password" if password else ""

    db = SessionLocal()

    db.execute(
        text(f"""
            UPDATE users
            SET
                username=:username,
                full_name=:full_name,
                role=:role,
                status=:status
                {password_sql}
            WHERE id=:user_id
        """),
        {
            "user_id": user_id,
            "username": username,
            "password": password,
            "full_name": full_name,
            "role": role,
            "status": status,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/users", status_code=303)


@app.get("/user/delete/{user_id}")
def user_delete(user_id: int, request: Request):

    blocked = admin_only_redirect(request)
    if blocked:
        return blocked

    current_username = request.session.get("user")

    db = SessionLocal()

    user = db.execute(
        text("SELECT username FROM users WHERE id=:user_id"),
        {"user_id": user_id},
    ).mappings().first()

    if user and user["username"] != current_username:
        db.execute(text("DELETE FROM users WHERE id=:user_id"), {"user_id": user_id})
        db.commit()

    db.close()

    return RedirectResponse("/users", status_code=303)


def save_employee_photo(photo: UploadFile = None):
    if not photo or not photo.filename:
        return ""

    upload_dir = "app/static/uploads/employees"
    os.makedirs(upload_dir, exist_ok=True)

    _, extension = os.path.splitext(photo.filename)
    filename = f"{uuid.uuid4().hex}{extension.lower()}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(photo.file.read())

    return f"/static/uploads/employees/{filename}"


@app.get("/hr")
def hr_dashboard(request: Request):
    db = SessionLocal()
    summary = db.execute(text("""
        SELECT
            COUNT(*) AS total_employees,
            SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) AS active_employees,
            COUNT(DISTINCT NULLIF(department, '')) AS department_count,
            COALESCE(SUM(advance_amount), 0) AS total_advances
        FROM employees
    """)).mappings().first()
    recent_employees = db.execute(text("""
        SELECT id, employee_code, employee_name, designation, department,
               joining_date, photo_path, status
        FROM employees
        ORDER BY joining_date DESC, id DESC
        LIMIT 6
    """)).mappings().all()
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="hr_dashboard.html",
        context={
            "request": request,
            "summary": summary,
            "recent_employees": recent_employees,
        },
    )


@app.get("/employee/profile/{employee_id}")
def employee_profile(employee_id: int, request: Request):
    db = SessionLocal()
    employee = db.execute(text("""
        SELECT * FROM employees WHERE id=:employee_id
    """), {"employee_id": employee_id}).mappings().first()
    if not employee:
        db.close()
        raise HTTPException(status_code=404, detail="Employee not found")
    attendance = db.execute(text("""
        SELECT * FROM employee_attendance
        WHERE employee_id=:employee_id
        ORDER BY attendance_year DESC, attendance_month DESC
        LIMIT 12
    """), {"employee_id": employee_id}).mappings().all()
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="employee_profile.html",
        context={"request": request, "employee": employee, "attendance": attendance},
    )


@app.get("/employee-advances")
def employee_advances(request: Request):
    db = SessionLocal()
    employees = db.execute(text("""
        SELECT id, employee_code, employee_name, designation, department,
               monthly_salary, advance_amount, photo_path, status
        FROM employees
        ORDER BY employee_name
    """)).mappings().all()
    total_advances = sum(float(item.advance_amount or 0) for item in employees)
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="employee_advances.html",
        context={
            "request": request,
            "employees": employees,
            "total_advances": total_advances,
        },
    )


@app.post("/employee-advance/update")
def employee_advance_update(
    employee_id: int = Form(...),
    advance_amount: float = Form(0),
):
    db = SessionLocal()
    db.execute(text("""
        UPDATE employees
        SET advance_amount=:advance_amount
        WHERE id=:employee_id
    """), {
        "employee_id": employee_id,
        "advance_amount": max(0, advance_amount),
    })
    db.commit()
    db.close()
    return RedirectResponse("/employee-advances", status_code=303)


@app.get("/employees")
def employees(request: Request):

    db = SessionLocal()

    employees = db.execute(text("""
        SELECT *
        FROM employees
        ORDER BY employee_name
    """)).mappings().all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="employees.html",
        context={"request": request, "employees": employees},
    )


@app.get("/employee/add")
def employee_add(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="employee_form.html",
        context={"request": request, "employee": None},
    )


@app.post("/employee/save")
async def employee_save(
    employee_code: str = Form(""),
    employee_name: str = Form(...),
    designation: str = Form(""),
    department: str = Form(""),
    joining_date: str = Form(""),
    monthly_salary: float = Form(0),
    advance_amount: float = Form(0),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    emergency_contact: str = Form(""),
    bank_name: str = Form(""),
    bank_account_no: str = Form(""),
    ifsc_code: str = Form(""),
    address: str = Form(""),
    status: str = Form("Active"),
    photo: UploadFile = File(None),
):

    photo_path = save_employee_photo(photo)

    db = SessionLocal()

    db.execute(
        text("""
            INSERT INTO employees
            (
                employee_code,
                employee_name,
                designation,
                department,
                joining_date,
                monthly_salary,
                advance_amount,
                phone,
                mobile,
                email,
                emergency_contact,
                bank_name,
                bank_account_no,
                ifsc_code,
                address,
                photo_path,
                status
            )
            VALUES
            (
                :employee_code,
                :employee_name,
                :designation,
                :department,
                :joining_date,
                :monthly_salary,
                :advance_amount,
                :phone,
                :mobile,
                :email,
                :emergency_contact,
                :bank_name,
                :bank_account_no,
                :ifsc_code,
                :address,
                :photo_path,
                :status
            )
        """),
        {
            "employee_code": employee_code,
            "employee_name": employee_name,
            "designation": designation,
            "department": department,
            "joining_date": joining_date if joining_date else None,
            "monthly_salary": monthly_salary,
            "advance_amount": advance_amount,
            "phone": phone,
            "mobile": mobile,
            "email": email,
            "emergency_contact": emergency_contact,
            "bank_name": bank_name,
            "bank_account_no": bank_account_no,
            "ifsc_code": ifsc_code,
            "address": address,
            "photo_path": photo_path,
            "status": status,
        },
    )

    db.commit()
    db.close()

    return RedirectResponse("/employees", status_code=303)


@app.get("/employee/edit/{employee_id}")
def employee_edit(employee_id: int, request: Request):

    db = SessionLocal()

    employee = db.execute(
        text("""
            SELECT *
            FROM employees
            WHERE id=:employee_id
        """),
        {"employee_id": employee_id},
    ).mappings().first()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="employee_form.html",
        context={"request": request, "employee": employee},
    )


@app.post("/employee/update")
async def employee_update(
    employee_id: int = Form(...),
    employee_code: str = Form(""),
    employee_name: str = Form(...),
    designation: str = Form(""),
    department: str = Form(""),
    joining_date: str = Form(""),
    monthly_salary: float = Form(0),
    advance_amount: float = Form(0),
    phone: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    emergency_contact: str = Form(""),
    bank_name: str = Form(""),
    bank_account_no: str = Form(""),
    ifsc_code: str = Form(""),
    address: str = Form(""),
    status: str = Form("Active"),
    photo: UploadFile = File(None),
):

    photo_path = save_employee_photo(photo)
    photo_sql = ", photo_path=:photo_path" if photo_path else ""

    db = SessionLocal()

    params = {
        "employee_id": employee_id,
        "employee_code": employee_code,
        "employee_name": employee_name,
        "designation": designation,
        "department": department,
        "joining_date": joining_date if joining_date else None,
        "monthly_salary": monthly_salary,
        "advance_amount": advance_amount,
        "phone": phone,
        "mobile": mobile,
        "email": email,
        "emergency_contact": emergency_contact,
        "bank_name": bank_name,
        "bank_account_no": bank_account_no,
        "ifsc_code": ifsc_code,
        "address": address,
        "status": status,
        "photo_path": photo_path,
    }

    db.execute(
        text(f"""
            UPDATE employees
            SET
                employee_code=:employee_code,
                employee_name=:employee_name,
                designation=:designation,
                department=:department,
                joining_date=:joining_date,
                monthly_salary=:monthly_salary,
                advance_amount=:advance_amount,
                phone=:phone,
                mobile=:mobile,
                email=:email,
                emergency_contact=:emergency_contact,
                bank_name=:bank_name,
                bank_account_no=:bank_account_no,
                ifsc_code=:ifsc_code,
                address=:address,
                status=:status
                {photo_sql}
            WHERE id=:employee_id
        """),
        params,
    )

    db.commit()
    db.close()

    return RedirectResponse("/employees", status_code=303)


@app.get("/employee/delete/{employee_id}")
def employee_delete(employee_id: int):

    db = SessionLocal()

    db.execute(text("DELETE FROM employee_attendance WHERE employee_id=:employee_id"), {"employee_id": employee_id})
    db.execute(text("DELETE FROM employees WHERE id=:employee_id"), {"employee_id": employee_id})

    db.commit()
    db.close()

    return RedirectResponse("/employees", status_code=303)


@app.get("/employee-attendance")
def employee_attendance(request: Request, month: int = 0, year: int = 0):

    today = date.today()

    if not month:
        month = today.month

    if not year:
        year = today.year

    db = SessionLocal()

    employees = db.execute(text("""
        SELECT
            id,
            employee_code,
            employee_name,
            designation,
            monthly_salary,
            advance_amount
        FROM employees
        WHERE status='Active'
        ORDER BY employee_name
    """)).mappings().all()

    attendance = db.execute(
        text("""
            SELECT *
            FROM employee_attendance
            WHERE attendance_month=:month
            AND attendance_year=:year
        """),
        {"month": month, "year": year},
    ).mappings().all()

    attendance_map = {row.employee_id: row for row in attendance}
    days_in_month = calendar.monthrange(year, month)[1]

    rows = []

    for employee in employees:
        item = dict(employee)
        item["attendance"] = attendance_map.get(employee.id)
        rows.append(item)

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="employee_attendance.html",
        context={
            "request": request,
            "employees": rows,
            "month": month,
            "year": year,
            "days_in_month": days_in_month,
            "years": list(range(today.year - 3, today.year + 2)),
            "months": [
                {"id": 1, "name": "January"},
                {"id": 2, "name": "February"},
                {"id": 3, "name": "March"},
                {"id": 4, "name": "April"},
                {"id": 5, "name": "May"},
                {"id": 6, "name": "June"},
                {"id": 7, "name": "July"},
                {"id": 8, "name": "August"},
                {"id": 9, "name": "September"},
                {"id": 10, "name": "October"},
                {"id": 11, "name": "November"},
                {"id": 12, "name": "December"},
            ],
        },
    )


@app.post("/employee-attendance/save")
async def employee_attendance_save(request: Request):

    form = await request.form()

    month = int(form.get("month"))
    year = int(form.get("year"))
    employee_ids = form.getlist("employee_id")

    db = SessionLocal()

    for employee_id in employee_ids:
        db.execute(
            text("""
                INSERT INTO employee_attendance
                (
                    employee_id,
                    attendance_month,
                    attendance_year,
                    present_days,
                    leave_days,
                    absent_days,
                    overtime_amount,
                    deduction_amount,
                    remarks
                )
                VALUES
                (
                    :employee_id,
                    :month,
                    :year,
                    :present_days,
                    :leave_days,
                    :absent_days,
                    :overtime_amount,
                    :deduction_amount,
                    :remarks
                )
                ON DUPLICATE KEY UPDATE
                    present_days=VALUES(present_days),
                    leave_days=VALUES(leave_days),
                    absent_days=VALUES(absent_days),
                    overtime_amount=VALUES(overtime_amount),
                    deduction_amount=VALUES(deduction_amount),
                    remarks=VALUES(remarks)
            """),
            {
                "employee_id": int(employee_id),
                "month": month,
                "year": year,
                "present_days": float(form.get(f"present_days_{employee_id}") or 0),
                "leave_days": float(form.get(f"leave_days_{employee_id}") or 0),
                "absent_days": float(form.get(f"absent_days_{employee_id}") or 0),
                "overtime_amount": float(form.get(f"overtime_amount_{employee_id}") or 0),
                "deduction_amount": float(form.get(f"deduction_amount_{employee_id}") or 0),
                "remarks": form.get(f"remarks_{employee_id}") or "",
            },
        )

    db.commit()
    db.close()

    return RedirectResponse(f"/employee-attendance?month={month}&year={year}", status_code=303)


@app.get("/salary-receipt")
def salary_receipt(request: Request, employee_id: int = 0, month: int = 0, year: int = 0):

    today = date.today()

    if not month:
        month = today.month

    if not year:
        year = today.year

    db = SessionLocal()

    employees = db.execute(text("""
        SELECT id, employee_name, employee_code
        FROM employees
        WHERE status='Active'
        ORDER BY employee_name
    """)).mappings().all()

    if not employee_id and employees:
        employee_id = employees[0].id

    employee = None
    attendance = None
    salary = None
    days_in_month = calendar.monthrange(year, month)[1]

    if employee_id:
        employee = db.execute(
            text("""
                SELECT *
                FROM employees
                WHERE id=:employee_id
            """),
            {"employee_id": employee_id},
        ).mappings().first()

        attendance = db.execute(
            text("""
                SELECT *
                FROM employee_attendance
                WHERE employee_id=:employee_id
                AND attendance_month=:month
                AND attendance_year=:year
            """),
            {"employee_id": employee_id, "month": month, "year": year},
        ).mappings().first()

        if employee:
            monthly_salary = float(employee.monthly_salary or 0)
            present_days = float(attendance.present_days or 0) if attendance else 0
            leave_days = float(attendance.leave_days or 0) if attendance else 0
            absent_days = float(attendance.absent_days or 0) if attendance else 0
            payable_days = present_days + leave_days
            per_day_salary = monthly_salary / days_in_month if days_in_month else 0
            earned_salary = per_day_salary * payable_days
            overtime_amount = float(attendance.overtime_amount or 0) if attendance else 0
            deduction_amount = float(attendance.deduction_amount or 0) if attendance else 0
            advance_amount = float(employee.advance_amount or 0)
            net_salary = earned_salary + overtime_amount - deduction_amount - advance_amount

            salary = {
                "days_in_month": days_in_month,
                "present_days": present_days,
                "leave_days": leave_days,
                "absent_days": absent_days,
                "payable_days": payable_days,
                "per_day_salary": per_day_salary,
                "earned_salary": earned_salary,
                "overtime_amount": overtime_amount,
                "deduction_amount": deduction_amount,
                "advance_amount": advance_amount,
                "net_salary": net_salary,
            }

    company = db.execute(text("SELECT * FROM company LIMIT 1")).mappings().first()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="salary_receipt.html",
        context={
            "request": request,
            "employees": employees,
            "employee": employee,
            "attendance": attendance,
            "salary": salary,
            "company": company,
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "years": list(range(today.year - 3, today.year + 2)),
            "months": [
                {"id": 1, "name": "January"},
                {"id": 2, "name": "February"},
                {"id": 3, "name": "March"},
                {"id": 4, "name": "April"},
                {"id": 5, "name": "May"},
                {"id": 6, "name": "June"},
                {"id": 7, "name": "July"},
                {"id": 8, "name": "August"},
                {"id": 9, "name": "September"},
                {"id": 10, "name": "October"},
                {"id": 11, "name": "November"},
                {"id": 12, "name": "December"},
            ],
        },
    )


@app.get("/login")
async def login_page(request: Request):
    blocked = require_company_selection(request)
    if blocked:
        return blocked

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": "",
            "tenant": selected_company_context(request),
        }
    )

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    blocked = require_company_selection(request)
    if blocked:
        return blocked

    db = SessionLocal()

    try:
        user = db.execute(
            text("""
                SELECT *
                FROM users
                WHERE username=:username
                AND password=:password
            """),
            {
                "username": username,
                "password": password
            }
        ).mappings().first()
    except Exception as error:
        db.close()

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": clean_database_error(error),
                "tenant": selected_company_context(request),
            },
        )

    db.close()

    if user:
        user_data = dict(user)

        if user_data.get("status", "Active") != "Active":
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,
                    "error": "User account is inactive.",
                    "tenant": selected_company_context(request),
                }
            )

        request.session["user"] = user_data.get("username", username)
        request.session["full_name"] = user_data.get("full_name") or user_data.get("username", username)
        request.session["role"] = user_data.get("role", "Admin")
        request.session["plan_name"] = request.session.get("tenant_plan_name", "")

        return RedirectResponse("/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": "Invalid Username or Password",
            "tenant": selected_company_context(request),
        }
    )

@app.get("/logout")
async def logout(request: Request):

    tenant_context = selected_company_context(request)
    tenant_database_url = request.session.get("tenant_database_url")
    request.session.clear()

    if tenant_database_url:
        request.session["tenant_company_code"] = tenant_context["company_code"]
        request.session["tenant_company_name"] = tenant_context["company_name"]
        request.session["tenant_company_tagline"] = tenant_context["company_tagline"]
        request.session["tenant_company_logo_url"] = tenant_context["company_logo_url"]
        request.session["tenant_company_banner_url"] = tenant_context["company_banner_url"]
        request.session["tenant_plan_name"] = tenant_context["plan_name"]
        request.session["tenant_database_url"] = tenant_database_url

    return RedirectResponse("/login", status_code=303)


@app.get("/sales/invoice/{sale_id}")
def sales_invoice(request: Request, sale_id: int):

    db = SessionLocal()

    # ==========================
    # Company Details
    # ==========================

    company = db.execute(text("""
        SELECT *
        FROM company
        LIMIT 1
    """)).mappings().first()

    # ==========================
    # Sales Header
    # ==========================

    sale = db.execute(text("""
        SELECT
            s.*,
            c.customer_name,
            c.company_name,
            c.mobile,
            c.email,
            c.address,
            c.gst_number
        FROM sales s

        LEFT JOIN customers c
            ON c.id = s.customer_id

        WHERE s.id=:sale_id
    """),
    {"sale_id": sale_id}
    ).mappings().first()

    if not sale:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    # ==========================
    # Invoice Items
    # ==========================

    items = db.execute(text("""

        SELECT

            si.*,

            p.product_name,

            p.product_code,

            p.hsn_code,

            p.gst_percent

        FROM sale_items si

        LEFT JOIN products p
            ON p.id = si.product_id

        WHERE si.sale_id=:sale_id

        ORDER BY si.id

    """),
    {"sale_id": sale_id}
    ).mappings().all()

    # Convert grand total to words
    amount_in_words = amount_to_words(sale.grand_total)
    
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="invoice.html",
        context={
            "request": request,
            "sale": sale,
            "items": items,
            "company": company,
            "amount_in_words": amount_in_words,
        }
    )
    
    
from num2words import num2words

def amount_to_words(amount):
    amount = float(amount)

    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    words = "Rupees " + num2words(rupees, lang="en_IN").title()

    if paise > 0:
        words += " And " + num2words(paise, lang="en_IN").title() + " Paise"

    words += " Only"

    return words

@app.post("/change-password")
async def change_password(request: Request):

    data = await request.json()

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    username = request.session.get("user")

    if not username:
        return JSONResponse({
            "success": False,
            "message": "Session Expired."
        })

    db = SessionLocal()

    # Check admin user
    user = db.execute(
        text("""
            SELECT *
            FROM users
            WHERE username=:username
        """),
        {"username": username}
    ).mappings().first()

    if not user:
        db.close()
        return JSONResponse({
            "success": False,
            "message": "User not found."
        })

    # Compare plain password
    if user["password"] != current_password:
        db.close()
        return JSONResponse({
            "success": False,
            "message": "Current Password is incorrect."
        })

    # Update new password
    db.execute(
        text("""
            UPDATE users
            SET password=:password
            WHERE username=:username
        """),
        {
            "password": new_password,
            "username": username
        }
    )

    db.commit()
    db.close()

    return JSONResponse({
        "success": True,
        "message": "Password Updated Successfully"
    })
    
@app.get("/change-password")
async def change_password_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={
            "request": request
        }
    )
