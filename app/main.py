from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.database import SessionLocal
from fastapi import Form
from fastapi.responses import RedirectResponse
from datetime import date, timedelta
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

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="SridheepamERP2026@SecretKey")

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


@app.get("/")
async def home(request: Request):

    if "user" in request.session:
        return RedirectResponse("/dashboard", status_code=303)

    return RedirectResponse("/login", status_code=303)

@app.get("/dashboard")
async def dashboard(request: Request):

    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "username": request.session["user"]
        }
    )


@app.get("/company")
def company(request: Request):

    db = SessionLocal()

    company = db.execute(text("SELECT * FROM company LIMIT 1")).fetchone()

    db.close()

    return templates.TemplateResponse(
        request=request, name="company.html", context={"company": company}
    )


@app.post("/company/save")
def save_company(
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


@app.get("/login")
async def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": ""
        }
    )

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

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

    db.close()

    if user:

        request.session["user"] = username

        return RedirectResponse("/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "error": "Invalid Username or Password"
        }
    )

@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

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