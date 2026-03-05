from flask import Flask, render_template, redirect, session, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import math
import os



app = Flask(__name__)
app.secret_key = "secret123"


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ================= USER MODEL =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


# ================= HOME =================
@app.route("/")
def home():
    return redirect(url_for("register"))


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Credentials"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template("register.html", error="Username already exists")

        # Create new user
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# EXPENSE CATEGORY CONFIGURATION (NEW FEATURE)
# ===================================================

EXPENSE_MAIN_CATEGORIES = [
    "Crop Production",
    "Labor",
    "Machinery",
    "Irrigation",
    "Transport",
    "Post Harvest",
    "Administrative",
    "Financial",
    "Government",
    "Miscellaneous"
]

EXPENSE_SUB_CATEGORIES = {
    "Crop Production": ["Seed", "Fertilizer", "Pesticide", "Herbicide"],
    "Labor": ["Permanent Labor", "Daily Wage", "Harvest Labor"],
    "Machinery": ["Fuel", "Maintenance", "Repair", "Spare Parts"],
    "Irrigation": ["Electricity", "Water Charges", "Pipe Repair"],
    "Transport": ["Market Transport", "Field Transport"],
    "Post Harvest": ["Storage", "Packaging"],
    "Administrative": ["Office Expense", "Stationery"],
    "Financial": ["Loan Interest", "Bank Charges"],
    "Government": ["Tax", "License Fee"],
    "Miscellaneous": ["Other"]
}



# ===================================================
# MODELS
# ===================================================

class Farmer(db.Model):
    farmer_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    village = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))

    lands = db.relationship('Land', backref='farmer', lazy=True)
    seasons = db.relationship('Season', backref='farmer', lazy=True)


class Land(db.Model):
    land_id = db.Column(db.Integer, primary_key=True)
    land_name = db.Column(db.String(100), nullable=False)
    total_area = db.Column(db.Float)
    unit = db.Column(db.String(50))
    soil_type = db.Column(db.String(50))
    irrigation_source = db.Column(db.String(50))
    land_status = db.Column(db.String(50))

    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.farmer_id'))

    seasons = db.relationship('Season', backref='land', lazy=True)
    expenses = db.relationship('Expense', backref='land', lazy=True)

    def __repr__(self):
        return f"<Land {self.land_name}>"

class Crop(db.Model):
    crop_id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100))
    variety = db.Column(db.String(100))
    duration_days = db.Column(db.Integer)
    expected_yield = db.Column(db.Float)
    crop_type = db.Column(db.String(100))

    seasons = db.relationship('Season', backref='crop', lazy=True)
    expenses = db.relationship('Expense', backref='crop', lazy=True)


class Season(db.Model):
    season_id = db.Column(db.Integer, primary_key=True)
    season_name = db.Column(db.String(50))
    year = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.farmer_id'))
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.crop_id'))
    land_id = db.Column(db.Integer, db.ForeignKey('land.land_id'))

    expenses = db.relationship('Expense', backref='season', lazy=True)


class Operation(db.Model):
    operation_id = db.Column(db.Integer, primary_key=True)

    operation_type = db.Column(db.String(100))
    operation_date = db.Column(db.Date)
    labor_used = db.Column(db.String(100))
    equipment_used = db.Column(db.String(100))
    notes = db.Column(db.Text)

    season = db.Column(db.String(100))   # ✅ ADD THIS
    land = db.Column(db.String(100))     # ✅ ADD THIS

class Equipment(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    sub_category = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    purchase_cost = db.Column(db.Float)
    vendor = db.Column(db.String(100))
    status = db.Column(db.String(50))

    maintenance_records = db.relationship('Maintenance', backref='equipment', lazy=True)
    fuel_logs = db.relationship('FuelLog', backref='equipment', lazy=True)


class Maintenance(db.Model):
    maintenance_id = db.Column(db.Integer, primary_key=True)
    maintenance_date = db.Column(db.Date)
    description = db.Column(db.String(200))
    cost = db.Column(db.Float)

    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id'))


class FuelLog(db.Model):
    fuel_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    fuel_type = db.Column(db.String(50))
    quantity = db.Column(db.Float)
    cost = db.Column(db.Float)

    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id'))


class Expense(db.Model):
    expense_id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date)

    main_category = db.Column(db.String(100))
    sub_category = db.Column(db.String(100))
    description = db.Column(db.String(200))

    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    rate = db.Column(db.Float)
    amount = db.Column(db.Float)

    expense_type = db.Column(db.String(50))
    supplier = db.Column(db.String(100))
    additional_cost = db.Column(db.Float)

    season_id = db.Column(db.Integer, db.ForeignKey('season.season_id'))
    land_id = db.Column(db.Integer, db.ForeignKey('land.land_id'))
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.crop_id')) 


    # ===================================================
# INCOME MODULE MODELS
# ===================================================


# 1️⃣ Crop Income
class CropIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.String(100))
    field_name = db.Column(db.String(100))
    crop_name = db.Column(db.String(100))
    harvest_batch = db.Column(db.String(100))
    quantity_harvested = db.Column(db.Float)
    quantity_sold = db.Column(db.Float)
    rate_per_unit = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    buyer_name = db.Column(db.String(100))
    market_name = db.Column(db.String(100))
    commission = db.Column(db.Float)
    transport_cost = db.Column(db.Float)
    net_income = db.Column(db.Float)
    total_income = db.Column(db.Float) 
    date = db.Column(db.DateTime, default=datetime.utcnow)


# 2️⃣ Livestock Income
class LivestockIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    milk_sales = db.Column(db.Float)
    egg_sales = db.Column(db.Float)
    meat_sales = db.Column(db.Float)
    animal_sales = db.Column(db.Float)
    manure_sales = db.Column(db.Float)
    total_income = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


# 3️⃣ By Product Sales
class ByProductIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    straw = db.Column(db.Float)
    husk = db.Column(db.Float)
    stems = db.Column(db.Float)
    cotton_waste = db.Column(db.Float)
    fodder = db.Column(db.Float)
    total_income = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


# 4️⃣ Government Subsidy
class GovernmentSubsidy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheme_name = db.Column(db.String(150))
    approved_amount = db.Column(db.Float)
    date_received = db.Column(db.Date)
    linked_crop = db.Column(db.String(100))
    date = db.Column(db.String(20))   


# 5️⃣ Insurance Claim
class InsuranceClaim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    claim_type = db.Column(db.String(100))
    amount_received = db.Column(db.Float)
    damage_reason = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


# 6️⃣ Equipment Rental Income
class EquipmentRentalIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100))
    rental_date = db.Column(db.Date)
    hours_used = db.Column(db.Float)
    rate_per_hour = db.Column(db.Float)
    total_income = db.Column(db.Float)


# 7️⃣ Seed Production Income
class SeedProductionIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100))
    quantity_produced = db.Column(db.Float)
    rate = db.Column(db.Float)
    total_income = db.Column(db.Float)
    certification_number = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)


# 8️⃣ Direct Retail Sales
class DirectRetailIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vegetables = db.Column(db.Float)
    fruits = db.Column(db.Float)
    organic_produce = db.Column(db.Float)
    total_income = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


# ================= GOVERNMENT SUBSIDY MODEL =================

class Subsidy(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    scheme_name = db.Column(db.String(200))

    approved_amount = db.Column(db.Float)

    date_received = db.Column(db.Date)

    # ===================================================
# WORKS MODULE (Advanced Version)
# ===================================================

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(db.String(50), unique=True)

    title = db.Column(db.String(200))
    category = db.Column(db.String(100))  # Pre-Sowing, Irrigation, Harvest etc
    stage = db.Column(db.String(100))  # Crop stage

    field_name = db.Column(db.String(100))
    subfield_name = db.Column(db.String(100))
    season = db.Column(db.String(100))
    crop = db.Column(db.String(100))
    variety = db.Column(db.String(100))

    area = db.Column(db.Float)  # acres/hectares

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    status = db.Column(db.String(50), default="Planned")
    priority = db.Column(db.String(50), default="Medium")

    input_cost = db.Column(db.Float, default=0)
    fuel_cost = db.Column(db.Float, default=0)

    total_cost = db.Column(db.Float, default=0)
    cost_per_acre = db.Column(db.Float, default=0)

    notes = db.Column(db.Text)

    # scheduling
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_days = db.Column(db.Integer)

    photo = db.Column(db.String(200))

    labors = db.relationship("WorkLabor", backref="work", cascade="all, delete")
    equipments = db.relationship("WorkEquipment", backref="work", cascade="all, delete")


# LABOR TRACKING
class WorkLabor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(db.Integer, db.ForeignKey('work.id'))

    labor_name = db.Column(db.String(100))
    hours_worked = db.Column(db.Float)
    wage_rate = db.Column(db.Float)
    attendance = db.Column(db.String(20))  # Present/Absent

    total_cost = db.Column(db.Float)


# EQUIPMENT TRACKING
class WorkEquipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(db.Integer, db.ForeignKey('work.id'))

    equipment_name = db.Column(db.String(100))
    hours_used = db.Column(db.Float)
    fuel_used = db.Column(db.Float)
    rental_cost = db.Column(db.Float)

    total_cost = db.Column(db.Float)




    # ===================================================
# INVENTORY MODULE
# ===================================================



# 1️⃣ SUPPLIER
class Supplier(db.Model):
    supplier_id = db.Column(db.Integer, primary_key=True)

    supplier_name = db.Column(db.String(150))
    contact_number = db.Column(db.String(50))
    address = db.Column(db.String(250))
    email = db.Column(db.String(120))
    gst_number = db.Column(db.String(50))

    inventory_items = db.relationship("InventoryItem", backref="supplier")
    purchase_orders = db.relationship("PurchaseOrder", backref="supplier")


# 2️⃣ WAREHOUSE (Enterprise Ready)
class Warehouse(db.Model):
    warehouse_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(200))


# 3️⃣ INVENTORY ITEM (MASTER TABLE)
class InventoryItem(db.Model):
    inventory_id = db.Column(db.Integer, primary_key=True)

    item_name = db.Column(db.String(150))
    category = db.Column(db.String(100))
    sub_category = db.Column(db.String(100))
    unit = db.Column(db.String(50))

    current_stock = db.Column(db.Float, default=0)
    min_stock_level = db.Column(db.Float)
    max_stock_level = db.Column(db.Float)

    purchase_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)

    expiry_date = db.Column(db.Date)
    storage_location = db.Column(db.String(150))

    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouse.warehouse_id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.supplier_id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("InventoryTransaction", backref="inventory")
    usages = db.relationship("WorkInventoryUsage", backref="inventory")
    purchase_items = db.relationship("PurchaseOrderItem", backref="inventory")

    barcode = db.Column(db.String(100), unique=True)
    qr_code = db.Column(db.String(200))



# 4️⃣ MULTI LOCATION STOCK
class InventoryStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouse.warehouse_id"))
    quantity = db.Column(db.Float)




# 4️⃣ INVENTORY TRANSACTION
class InventoryTransaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)

    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))

    transaction_type = db.Column(db.String(50))  # IN / OUT / ADJUSTMENT
    quantity = db.Column(db.Float)
    balance_after = db.Column(db.Float)

    date = db.Column(db.DateTime, default=datetime.utcnow)

    reference_type = db.Column(db.String(100))  # Work / Purchase / Damage / Sale
    reference_id = db.Column(db.Integer)

    notes = db.Column(db.Text)


# 5️⃣ WORK INVENTORY USAGE
class WorkInventoryUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(db.Integer, db.ForeignKey("work.id"))
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))

    quantity_used = db.Column(db.Float)
    unit = db.Column(db.String(50))
    cost = db.Column(db.Float)


# 6️⃣ PURCHASE ORDER
class PurchaseOrder(db.Model):
    po_id = db.Column(db.Integer, primary_key=True)

    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.supplier_id"))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(50))


# 7️⃣ PURCHASE ORDER ITEM
class PurchaseOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    po_id = db.Column(db.Integer, db.ForeignKey("purchase_order.po_id"))
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))

    quantity = db.Column(db.Float)
    rate = db.Column(db.Float)
    total_cost = db.Column(db.Float)


# 8️⃣ DAMAGE LOG
class DamageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))
    quantity = db.Column(db.Float)
    reason = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


    # 6️⃣ IoT TANK
class IoTTank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory_item.inventory_id"))
    tank_name = db.Column(db.String(100))
    capacity = db.Column(db.Float)
    current_level = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


    # ================= WEATHER MODEL =================

class Weather(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    wind_speed = db.Column(db.Float)

    cloud_cover = db.Column(db.Float)
    uv_index = db.Column(db.Float)

    date = db.Column(db.DateTime, default=datetime.utcnow)


# ===================================================
# WEATHER MODULE
# ===================================================

class WeatherCurrent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall_today = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    cloud_cover = db.Column(db.Float)
    uv_index = db.Column(db.Float)

    condition = db.Column(db.String(50))  # Sunny / Rainy / Cloudy

    location = db.Column(db.String(100))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= FORECAST MODEL =================

# ================= WEATHER FORECAST MODEL =================

class WeatherForecast(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    forecast_date = db.Column(db.Date)

    temperature_min = db.Column(db.Float)

    temperature_max = db.Column(db.Float)

    rainfall_prediction = db.Column(db.Float)

    wind_speed = db.Column(db.Float)

    storm_warning = db.Column(db.Boolean, default=False)


class RainfallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)
    rainfall_mm = db.Column(db.Float)
    location = db.Column(db.String(100))


class SoilMoistureSensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    field_name = db.Column(db.String(100))
    sensor_id = db.Column(db.String(100))

    moisture_level = db.Column(db.Float)
    soil_temperature = db.Column(db.Float)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class WeatherAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    alert_type = db.Column(db.String(100))  # Heatwave / Frost / Heavy Rain
    severity = db.Column(db.String(50))     # Low / Medium / High
    message = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # ===================================================
# SATELLITE WEATHER DATA
# ===================================================

class SatelliteWeather(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    location = db.Column(db.String(100))

    ndvi_index = db.Column(db.Float)  # vegetation health
    land_surface_temp = db.Column(db.Float)
    evapotranspiration = db.Column(db.Float)

    rainfall_estimate = db.Column(db.Float)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


    # ===================================================
# IoT WEATHER STATION
# ===================================================

class IoTWeatherStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    station_name = db.Column(db.String(100))
    location = db.Column(db.String(100))

    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    pressure = db.Column(db.Float)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


    # ===================================================
# AI YIELD PREDICTION
# ===================================================

class YieldPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    crop_name = db.Column(db.String(100))
    field_name = db.Column(db.String(100))

    predicted_yield = db.Column(db.Float)
    confidence_level = db.Column(db.Float)

    based_on_rainfall = db.Column(db.Float)
    based_on_temperature = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    # ===================================================
# CROP ADVISORY SYSTEM
# ===================================================

class CropAdvisory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    crop_name = db.Column(db.String(100))
    advisory_type = db.Column(db.String(100))  # Irrigation / Fertilizer / Pest
    message = db.Column(db.String(300))

    risk_level = db.Column(db.String(50))  # Low / Medium / High

    created_at = db.Column(db.DateTime, default=datetime.utcnow)





# ================= LOAN MASTER =================
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    loan_id = db.Column(db.String(50), unique=True, nullable=False)
    loan_type = db.Column(db.String(50))
    loan_category = db.Column(db.String(50))

    bank_name = db.Column(db.String(100))
    branch_name = db.Column(db.String(100))
    account_number = db.Column(db.String(100))

    sanction_date = db.Column(db.Date)
    disbursement_date = db.Column(db.Date)

    loan_amount = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    tenure_months = db.Column(db.Integer)

    repayment_type = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Active")

    # Linking
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.farmer_id'))
    season_id = db.Column(db.Integer, nullable=True)
    equipment_id = db.Column(db.Integer, nullable=True)
    land_id = db.Column(db.Integer, nullable=True)

    emis = db.relationship("LoanEMI", backref="loan", lazy=True)
    payments = db.relationship("LoanPayment", backref="loan", lazy=True)

    def calculate_emi(self):
        P = self.loan_amount
        r = (self.interest_rate / 100) / 12
        n = self.tenure_months

        if r == 0:
            return P / n

        emi = P * r * (1 + r)**n / ((1 + r)**n - 1)
        return round(emi, 2)
      



# ================= EMI TABLE =================
class LoanEMI(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))
    due_date = db.Column(db.Date)

    emi_amount = db.Column(db.Float)
    principal_component = db.Column(db.Float)
    interest_component = db.Column(db.Float)

    remaining_balance = db.Column(db.Float)
    status = db.Column(db.String(20), default="Pending")



# ================= LOAN PAYMENTS =================
class LoanPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))

    payment_date = db.Column(db.Date)
    amount_paid = db.Column(db.Float)

    payment_mode = db.Column(db.String(50))
    receipt_number = db.Column(db.String(100))
    late_fee = db.Column(db.Float, default=0)

    remaining_balance = db.Column(db.Float)



    # ================= GOVERNMENT SCHEME =================
class LoanScheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))

    scheme_name = db.Column(db.String(100))
    subsidy_received = db.Column(db.Float)
    interest_subsidy = db.Column(db.Float)
    benefit_amount = db.Column(db.Float)



    # ================= COLLATERAL =================
class LoanCollateral(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'))

    collateral_type = db.Column(db.String(50))
    description = db.Column(db.String(200))
    guarantor_name = db.Column(db.String(100))
    guarantor_contact = db.Column(db.String(100))



# ===================================================
# HELPER FUNCTIONS
# ===================================================

def generate_qr(data, filename):
    if not os.path.exists("static/qrcodes"):
        os.makedirs("static/qrcodes")

    qr = qrcode.make(data)
    path = os.path.join("static/qrcodes", filename)
    qr.save(path)
    return filename


def update_stock(inventory_id, quantity, transaction_type,
                 reference_type=None, reference_id=None, notes=None):

    item = InventoryItem.query.get(inventory_id)

    if transaction_type == "IN":
        item.current_stock += quantity
    elif transaction_type == "OUT":
        item.current_stock -= quantity

    transaction = InventoryTransaction(
        inventory_id=inventory_id,
        transaction_type=transaction_type,
        quantity=quantity,
        balance_after=item.current_stock,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes
    )

    db.session.add(transaction)
    db.session.commit()

    auto_reorder_check()


def auto_reorder_check():
    low_items = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.min_stock_level
    ).all()

    for item in low_items:
        po = PurchaseOrder(
            supplier_id=item.supplier_id,
            status="Auto-Created"
        )
        db.session.add(po)
        db.session.commit()

        po_item = PurchaseOrderItem(
            po_id=po.po_id,
            inventory_id=item.inventory_id,
            quantity=item.max_stock_level - item.current_stock,
            rate=item.purchase_price,
            total_cost=(item.max_stock_level - item.current_stock) * item.purchase_price
        )

        db.session.add(po_item)
        db.session.commit()

        po_item = PurchaseOrderItem(
            po_id=po.po_id,
            inventory_id=item.inventory_id,
            quantity=item.max_stock_level - item.current_stock,
            rate=item.purchase_price,
            total_cost=(item.max_stock_level - item.current_stock) * item.purchase_price
        )

        db.session.add(po_item)
        db.session.commit()

    


# ===================================================
# WEATHER ERP LOGIC
# ===================================================

def calculate_rain_deficit(expected_rain, actual_rain):
    return expected_rain - actual_rain


def irrigation_recommendation(temp, humidity, soil_moisture):
    if soil_moisture < 30:
        return "Dry Soil - Irrigation Needed"
    elif soil_moisture > 70:
        return "Overwatering Alert"
    elif temp > 35:
        return "High Temperature - Increase Water Supply"
    else:
        return "Irrigation Normal"


def pest_risk_prediction(temp, humidity, rainfall):
    if humidity > 80 and temp > 25:
        return "High Fungal Disease Risk"
    elif rainfall > 20:
        return "Pest Outbreak Risk"
    else:
        return "Low Risk"


def extreme_weather_check(temp, rainfall, wind):
    alerts = []

    if temp > 42:
        alerts.append("Heatwave Alert")
    if temp < 5:
        alerts.append("Frost Alert")
    if rainfall > 50:
        alerts.append("Heavy Rain Alert")
    if wind > 60:
        alerts.append("High Wind Warning")

    return alerts



# ===================================================
# AI INTELLIGENCE LOGIC
# ===================================================

def ai_yield_estimation(rainfall, temperature, soil_moisture):
    base_yield = 100

    if rainfall < 50:
        base_yield -= 20
    if temperature > 38:
        base_yield -= 15
    if soil_moisture < 30:
        base_yield -= 10

    return base_yield


def generate_crop_advisory(temp, humidity, rainfall):
    if rainfall > 40:
        return "Avoid fertilizer application before heavy rain", "High"
    elif humidity > 85:
        return "Fungal disease risk - Spray preventive fungicide", "Medium"
    elif temp > 40:
        return "Heat stress - Increase irrigation frequency", "High"
    else:
        return "Crop conditions stable", "Low"



def generate_emi_schedule(loan):
    emi_amount = loan.calculate_emi()
    balance = loan.loan_amount
    r = (loan.interest_rate / 100) / 12

    for month in range(loan.tenure_months):
        interest = balance * r
        principal = emi_amount - interest
        balance -= principal

        emi = LoanEMI(
            loan_id=loan.id,
            due_date=loan.disbursement_date,
            emi_amount=emi_amount,
            principal_component=round(principal, 2),
            interest_component=round(interest, 2),
            remaining_balance=round(balance, 2)
        )

        db.session.add(emi)

    db.session.commit()



# ===================================================
# FARMER
# ===================================================

@app.route("/farmer")
def farmer():
    return render_template("farmer_profile.html", farmers=Farmer.query.all())

@app.route("/add_farmer", methods=["POST"])
def add_farmer():
    farmer = Farmer(
        full_name=request.form.get("full_name"),
        mobile=request.form.get("mobile"),
        village=request.form.get("village"),
        district=request.form.get("district"),
        state=request.form.get("state")
    )
    db.session.add(farmer)
    db.session.commit()
    return redirect(url_for("farmer"))


@app.route("/delete_farmer/<int:id>")
def delete_farmer(id):
    farmer = Farmer.query.get_or_404(id)
    db.session.delete(farmer)
    db.session.commit()
    return redirect(url_for("farmer"))





# ===================================================
# LAND
# ===================================================

@app.route("/land")
def land():
    return render_template("land.html",
                           lands=Land.query.all(),
                           farmers=Farmer.query.all())

@app.route("/add_land", methods=["POST"])
def add_land():
    land = Land(
        land_name=request.form.get("land_name"),
        total_area=request.form.get("total_area"),
        unit=request.form.get("unit"),
        soil_type=request.form.get("soil_type"),
        irrigation_source=request.form.get("irrigation_source"),
        land_status=request.form.get("land_status"),
        farmer_id=request.form.get("farmer_id")
    )
    db.session.add(land)
    db.session.commit()
    return redirect(url_for("land"))


@app.route("/delete_land/<int:id>")
def delete_land(id):
    land = Land.query.get_or_404(id)
    db.session.delete(land)
    db.session.commit()
    return redirect(url_for("land"))

# ===================================================
# CROPS
# ===================================================

@app.route("/crops")
def crops():
    return render_template("crops.html", crops=Crop.query.all())

@app.route("/add_crop", methods=["POST"])
def add_crop():
    crop = Crop(
        crop_name=request.form.get("crop_name"),
        variety=request.form.get("variety"),
        duration_days=request.form.get("duration_days"),
        expected_yield=request.form.get("expected_yield"),
        crop_type=request.form.get("crop_type")
    )
    db.session.add(crop)
    db.session.commit()
    return redirect(url_for("crops"))

@app.route("/delete_crop/<int:id>")
def delete_crop(id):
    crop = Crop.query.get_or_404(id)
    db.session.delete(crop)
    db.session.commit()
    return redirect(url_for("crops"))

# ===================================================
# SEASONS
# ===================================================

@app.route("/seasons")
def seasons():
    return render_template("seasons.html",
                           seasons=Season.query.all(),
                           farmers=Farmer.query.all(),
                           crops=Crop.query.all(),
                           lands=Land.query.all())

@app.route("/add_season", methods=["POST"])
def add_season():
    season = Season(
        season_name=request.form.get("season_name"),
        year=request.form.get("year"),
        start_date=datetime.strptime(request.form.get("start_date"), "%Y-%m-%d") if request.form.get("start_date") else None,
        end_date=datetime.strptime(request.form.get("end_date"), "%Y-%m-%d") if request.form.get("end_date") else None,
        farmer_id=request.form.get("farmer_id"),
        crop_id=request.form.get("crop_id"),
        land_id=request.form.get("land_id")
    )
    db.session.add(season)
    db.session.commit()
    return redirect(url_for("seasons"))

# ===================================================
# OPERATIONS
# ===================================================

@app.route("/operations")
def operations():
    return render_template("operations.html",
                           operations=Operation.query.all(),
                           seasons=Season.query.all(),
                           lands=Land.query.all())

@app.route("/add_operation", methods=["POST"])
def add_operation():
    operation = Operation(
        operation_type=request.form.get("operation_type"),
        operation_date=datetime.strptime(
            request.form.get("operation_date"),
            "%Y-%m-%d"
        ) if request.form.get("operation_date") else None,
        labor_used=request.form.get("labor_used"),
        equipment_used=request.form.get("equipment_used"),
        notes=request.form.get("notes"),
        season=request.form.get("season"),   # matches model
        land=request.form.get("land")        # matches model
    )

    db.session.add(operation)
    db.session.commit()

    return redirect(url_for("operations"))


@app.route("/delete_operation/<int:id>")
def delete_operation(id):
    operation = Operation.query.get_or_404(id)
    db.session.delete(operation)
    db.session.commit()
    return redirect(url_for("operations"))
# ===================================================
# EQUIPMENT
# ===================================================

@app.route("/equipment")
def equipment():
    equipments = Equipment.query.all()

    # Yearly maintenance summary
    yearly_data = {}
    for eq in equipments:
        for m in eq.maintenance_records:
            if m.maintenance_date:
                year = m.maintenance_date.year
                yearly_data[year] = yearly_data.get(year, 0) + (m.cost or 0)

    # Fuel summary per equipment
    fuel_summary = {}
    for eq in equipments:
        fuel_summary[eq.name] = sum(f.cost or 0 for f in eq.fuel_logs)

    return render_template(
        "equipment.html",
        equipments=equipments,
        yearly_data=yearly_data,
        fuel_summary=fuel_summary
    )


@app.route("/add_equipment", methods=["POST"])
def add_equipment():
    equipment = Equipment(
        name=request.form.get("name"),
        category=request.form.get("category"),
        sub_category=request.form.get("sub_category"),
        purchase_date=datetime.strptime(request.form.get("purchase_date"), "%Y-%m-%d") if request.form.get("purchase_date") else None,
        purchase_cost=float(request.form.get("purchase_cost") or 0),
        vendor=request.form.get("vendor"),
        status=request.form.get("status")
    )
    db.session.add(equipment)
    db.session.commit()
    return redirect(url_for("equipment"))


@app.route("/add_maintenance", methods=["POST"])
def add_maintenance():
    maintenance = Maintenance(
        maintenance_date=datetime.strptime(request.form.get("maintenance_date"), "%Y-%m-%d") if request.form.get("maintenance_date") else None,
        description=request.form.get("description"),
        cost=float(request.form.get("cost") or 0),
        equipment_id=request.form.get("equipment_id")
    )
    db.session.add(maintenance)
    db.session.commit()
    return redirect(url_for("equipment"))


@app.route("/add_fuel", methods=["POST"])
def add_fuel():
    fuel = FuelLog(
        date=datetime.strptime(request.form.get("date"), "%Y-%m-%d") if request.form.get("date") else None,
        fuel_type=request.form.get("fuel_type"),
        quantity=float(request.form.get("quantity") or 0),
        cost=float(request.form.get("cost") or 0),
        equipment_id=request.form.get("equipment_id")
    )
    db.session.add(fuel)
    db.session.commit()
    return redirect(url_for("equipment"))


@app.route("/delete_equipment/<int:id>")
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    db.session.delete(equipment)
    db.session.commit()
    return redirect(url_for("equipment"))


# ===================================================
# EXPENSES
# ===================================================

@app.route("/expenses")
def expenses():

    selected_category = request.args.get("category")

    all_expenses = Expense.query.all()
    seasons = Season.query.all()
    lands = Land.query.all()
    crops = Crop.query.all()

    # ================= CALCULATIONS =================

    total_expense = 0

    expense_per_season = {}
    expense_per_crop = {}
    expense_per_land = {}
    expense_per_category = {}

    fixed_cost = 0
    variable_cost = 0

    for e in all_expenses:

        quantity = e.quantity or 0
        rate = e.rate or 0
        additional = e.additional_cost or 0

        amount = (quantity * rate) + additional

        total_expense += amount

        # Expense Type
        if e.expense_type == "Fixed":
            fixed_cost += amount
        else:
            variable_cost += amount

        # Season analytics
        if e.season:
            season_name = e.season.season_name
            expense_per_season[season_name] = expense_per_season.get(season_name, 0) + amount

        # Crop analytics
        if e.crop:
            crop_name = e.crop.crop_name
            expense_per_crop[crop_name] = expense_per_crop.get(crop_name, 0) + amount

        # Land analytics
        if e.land:
            land_name = e.land.land_name
            expense_per_land[land_name] = expense_per_land.get(land_name, 0) + amount

        # Category analytics
        if e.main_category:
            cat = e.main_category
            expense_per_category[cat] = expense_per_category.get(cat, 0) + amount

    return render_template(
        "expenses.html",
        expenses=all_expenses,
        seasons=seasons,
        lands=lands,
        crops=crops,
        total_expense=total_expense,
        expense_per_season=expense_per_season,
        expense_per_crop=expense_per_crop,
        expense_per_land=expense_per_land,
        expense_per_category=expense_per_category,
        fixed_cost=fixed_cost,
        variable_cost=variable_cost
    )


@app.route("/delete_expense_record/<int:id>")
def delete_expense_record(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("expenses"))

    # ==========================
    # CALCULATIONS
    # ==========================

    total_expense = sum(e.amount or 0 for e in all_expenses)

    expense_per_season = {
        s.season_name: sum(e.amount or 0 for e in s.expenses)
        for s in seasons
    }

    expense_per_crop = {
        c.crop_name: sum(e.amount or 0 for e in c.expenses)
        for c in crops
    }

    expense_per_land = {
        l.land_name: sum(e.amount or 0 for e in l.expenses)
        for l in lands
    }

    expense_per_category = {}
    expense_per_subcategory = {}

    for e in all_expenses:
        main_key = e.main_category or "Other"
        sub_key = e.sub_category or "Other"

        expense_per_category[main_key] = expense_per_category.get(main_key, 0) + (e.amount or 0)
        expense_per_subcategory[sub_key] = expense_per_subcategory.get(sub_key, 0) + (e.amount or 0)

    fixed_cost = sum(e.amount or 0 for e in all_expenses if e.expense_type == "Fixed")
    variable_cost = sum(e.amount or 0 for e in all_expenses if e.expense_type == "Variable")

    return render_template(
        "expenses.html",
        expenses=all_expenses,
        seasons=seasons,
        lands=lands,
        crops=crops,
        total_expense=total_expense,
        expense_per_season=expense_per_season,
        expense_per_crop=expense_per_crop,
        expense_per_land=expense_per_land,
        expense_per_category=expense_per_category,
        expense_per_subcategory=expense_per_subcategory,
        fixed_cost=fixed_cost,
        variable_cost=variable_cost,
        EXPENSE_MAIN_CATEGORIES=EXPENSE_MAIN_CATEGORIES,
        EXPENSE_SUB_CATEGORIES=EXPENSE_SUB_CATEGORIES
    )


@app.route("/add_expense", methods=["POST"])
def add_expense():

    quantity = float(request.form.get("quantity") or 0)
    rate = float(request.form.get("rate") or 0)
    additional_cost = float(request.form.get("additional_cost") or 0)

    total_amount = (quantity * rate) + additional_cost

    expense = Expense(
        expense_date=datetime.strptime(
            request.form.get("expense_date"), "%Y-%m-%d"
        ) if request.form.get("expense_date") else None,

        main_category=request.form.get("main_category"),
        sub_category=request.form.get("sub_category"),
        description=request.form.get("description"),

        quantity=quantity,
        unit=request.form.get("unit"),
        rate=rate,
        amount=total_amount,

        expense_type=request.form.get("expense_type"),
        supplier=request.form.get("supplier"),
        additional_cost=additional_cost,

        season_id=request.form.get("season_id") or None,
        land_id=request.form.get("land_id") or None,
        crop_id=request.form.get("crop_id") or None
    )

    db.session.add(expense)
    db.session.commit()

    return redirect(url_for("expenses"))


@app.route("/delete_expense/<int:id>")
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("expenses"))


@app.route("/add_crop_income", methods=["POST"])
def add_crop_income():

    season = request.form.get("season")
    field_name = request.form.get("field_name")
    crop_name = request.form.get("crop_name")

    quantity_harvested = float(request.form.get("quantity_harvested") or 0)
    quantity_sold = float(request.form.get("quantity_sold") or 0)
    rate_per_unit = float(request.form.get("rate_per_unit") or 0)
    commission = float(request.form.get("commission") or 0)
    transport_cost = float(request.form.get("transport_cost") or 0)

    gross_income = quantity_sold * rate_per_unit
    total_income = gross_income - commission - transport_cost

    new_income = CropIncome(
        season=season,
        field_name=field_name,
        crop_name=crop_name,
        quantity_harvested=quantity_harvested,
        quantity_sold=quantity_sold,
        rate_per_unit=rate_per_unit,
        commission=commission,
        transport_cost=transport_cost,
        total_income=total_income
    )

    db.session.add(new_income)
    db.session.commit()

    return redirect(url_for("income_dashboard"))


@app.route("/add_livestock_income", methods=["POST"])
def add_livestock_income():

    # Safely get values (no crash if empty)
    milk = float(request.form.get('milk_sales') or 0)
    egg = float(request.form.get('egg_sales') or 0)
    meat = float(request.form.get('meat_sales') or 0)
    animal = float(request.form.get('animal_sales') or 0)
    manure = float(request.form.get('manure_sales') or 0)

    print("Livestock route HIT")

    # Calculate total
    total = milk + egg + meat + animal + manure

    # Save to database
    data = LivestockIncome(
        milk_sales=milk,
        egg_sales=egg,
        meat_sales=meat,
        animal_sales=animal,
        manure_sales=manure,
        total_income=total
    )

    db.session.add(data)
    db.session.commit()

    return redirect(url_for("income_dashboard"))


@app.route("/add_subsidy", methods=["POST"])
def add_subsidy():

    scheme = request.form.get("scheme_name")
    amount = float(request.form.get("approved_amount") or 0)
    date = request.form.get("date")

    data = GovernmentSubsidy(
        scheme_name=scheme,
        approved_amount=amount,
        date=date
    )

    db.session.add(data)
    db.session.commit()

    return redirect(url_for("income_dashboard"))


# ============================
# INCOME DASHBOARD ROUTE
# ============================

@app.route("/income")
def income_dashboard():
    crop_income = CropIncome.query.all()
    livestock_income = LivestockIncome.query.all()
    byproduct_income = ByProductIncome.query.all()
    subsidy = GovernmentSubsidy.query.all()
    insurance = InsuranceClaim.query.all()
    rental = EquipmentRentalIncome.query.all()
    seed_income = SeedProductionIncome.query.all()
    retail = DirectRetailIncome.query.all()

    print("Livestock records:", livestock_income)

    return render_template(
        "income.html",
        crop_income=crop_income,
        livestock_income=livestock_income,
        byproduct_income=byproduct_income,
        subsidy=subsidy,
        insurance=insurance,
        rental=rental,
        seed_income=seed_income,
        retail=retail
    )


# ================= DELETE SUBSIDY =================

@app.route("/delete_subsidy/<int:id>")
def delete_subsidy(id):

    subsidy = GovernmentSubsidy.query.get_or_404(id)

    db.session.delete(subsidy)
    db.session.commit()

    return redirect(url_for("income_dashboard"))


@app.route("/add_work", methods=["POST"])
def add_work():

    field_name = request.form.get("field_name")
    other_field = request.form.get("other_field_name")

    if field_name == "other" and other_field:
        field_name = other_field.strip()

    category = request.form.get("category")
    other_category = request.form.get("other_category")

    if category == "other" and other_category:
        category = other_category.strip()

    area = float(request.form.get("area") or 0)
    input_cost = float(request.form.get("input_cost") or 0)
    fuel_cost = float(request.form.get("fuel_cost") or 0)

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = None

    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = None

    new_work = Work(
        title=request.form.get("title"),
        category=category,
        stage=request.form.get("stage"),
        field_name=field_name,
        season=request.form.get("season"),
        crop=request.form.get("crop"),
        variety=request.form.get("variety"),
        area=area,
        start_date=start_date,
        end_date=end_date,
        priority=request.form.get("priority"),
        input_cost=input_cost,
        fuel_cost=fuel_cost,
        is_recurring=True if request.form.get("is_recurring") else False,
        recurrence_days=request.form.get("recurrence_days"),
        notes=request.form.get("notes")
    )

    db.session.add(new_work)
    db.session.commit()

    # ✅ FIXED LINE
    return redirect(url_for("works_dashboard"))

@app.route("/add_work_labor/<int:work_id>", methods=["POST"])
def add_work_labor(work_id):

    hours = float(request.form['hours'])
    wage = float(request.form['wage'])

    total = hours * wage

    labor = WorkLabor(
        work_id=work_id,
        labor_name=request.form['labor_name'],
        hours_worked=hours,
        wage_rate=wage,
        attendance=request.form['attendance'],
        total_cost=total
    )

    db.session.add(labor)
    db.session.commit()

    update_work_cost(work_id)

    return redirect(url_for("works_dashboard"))


@app.route("/add_work_equipment/<int:work_id>", methods=["POST"])
def add_work_equipment(work_id):

    rental = float(request.form['rental_cost'])
    fuel = float(request.form['fuel_used'])

    total = rental + fuel

    equipment = WorkEquipment(
        work_id=work_id,
        equipment_name=request.form['equipment_name'],
        hours_used=request.form['hours_used'],
        fuel_used=fuel,
        rental_cost=rental,
        total_cost=total
    )

    db.session.add(equipment)
    db.session.commit()

    update_work_cost(work_id)

    return redirect(url_for("works_dashboard"))


def update_work_cost(work_id):
    work = Work.query.get(work_id)

    labor_cost = sum(l.total_cost for l in work.labors)
    equipment_cost = sum(e.total_cost for e in work.equipments)

    total = labor_cost + equipment_cost + work.input_cost + work.fuel_cost

    work.total_cost = total

    if work.area and work.area > 0:
        work.cost_per_acre = total / work.area
    else:
        work.cost_per_acre = 0

    db.session.commit()


# OUTSIDE the function (no indentation)
# ===================================================
# WORKS DASHBOARD ROUTE (FIXED)
# ===================================================

@app.route("/workers")
def works_dashboard():

    works = Work.query.order_by(Work.start_date.desc()).all()

    total_works = Work.query.count()
    completed = Work.query.filter_by(status="Completed").count()

    completion_rate = 0
    if total_works > 0:
        completion_rate = (completed / total_works) * 100

    # Fetch lands correctly
    lands = Land.query.all()

    return render_template(
        "works.html",
        works=works,
        total_works=total_works,
        completion_rate=completion_rate,
        lands=lands
    )


@app.route("/workers_report")
def works_report():

    avg_cost = db.session.query(db.func.avg(Work.total_cost)).scalar()
    total_cost = db.session.query(db.func.sum(Work.total_cost)).scalar()

    return render_template("workers_report.html",
                           avg_cost=avg_cost,
                           total_cost=total_cost)








@app.route("/add_work_inventory/<int:work_id>", methods=["POST"])
def add_work_inventory(work_id):

    inventory_id = int(request.form['inventory_id'])
    quantity = float(request.form['quantity'])

    item = InventoryItem.query.get(inventory_id)
    cost = quantity * item.purchase_price

    usage = WorkInventoryUsage(
        work_id=work_id,
        inventory_id=inventory_id,
        quantity_used=quantity,
        unit=item.unit,
        cost=cost
    )

    db.session.add(usage)
    update_stock(inventory_id, quantity, "OUT", "Work", work_id, "Used in Work")
    db.session.commit()
    update_work_cost(work_id)
    return redirect(url_for("works_dashboard"))



@app.route("/create_purchase_order", methods=["POST"])
def create_purchase_order():

    po = PurchaseOrder(
        supplier_id=request.form['supplier_id'],
        status="Pending"
    )

    db.session.add(po)
    db.session.commit()

    return redirect(url_for("inventory_dashboard"))



@app.route("/receive_po_item/<int:inventory_id>", methods=["POST"])
def receive_po_item(inventory_id):

    quantity = float(request.form['quantity'])

    update_stock(inventory_id, quantity, "IN", "Purchase", None, "PO Received")

    return redirect(url_for("inventory_dashboard"))


@app.route("/delete_work/<int:id>")
def delete_work(id):
    work = Works.query.get_or_404(id)
    db.session.delete(work)
    db.session.commit()
    return redirect(url_for("works_dashboard"))


@app.route("/inventory")
def inventory_dashboard():

    items = InventoryItem.query.all()
    warehouses = Warehouse.query.all()

    low_stock = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.min_stock_level
    ).all()

    return render_template(
        "inventory.html",
        items=items,
        low_stock=low_stock,
        warehouses=warehouses
    )

import uuid

@app.route("/add_inventory_item", methods=["POST"])
def add_inventory_item():

    barcode_value = str(uuid.uuid4())[:12]

    item = InventoryItem(
        item_name=request.form['item_name'],
        category=request.form['category'],
        unit=request.form['unit'],
        purchase_price=request.form['purchase_price'],
        min_stock_level=request.form['min_stock_level'],
        barcode=barcode_value
    )

    db.session.add(item)
    db.session.commit()

    return redirect(url_for("inventory_dashboard"))




@app.route("/stock_in/<int:inventory_id>", methods=["POST"])
def stock_in(inventory_id):

    quantity = float(request.form['quantity'])
    update_stock(inventory_id, quantity, "IN", "Manual", None, "Stock Added")

    return redirect(url_for("inventory_dashboard"))




@app.route("/stock_out/<int:inventory_id>", methods=["POST"])
def stock_out(inventory_id):

    quantity = float(request.form['quantity'])
    update_stock(inventory_id, quantity, "OUT", "Manual", None, "Stock Removed")

    return redirect(url_for("inventory_dashboard"))




@app.route("/transfer_stock", methods=["POST"])
def transfer_stock():

    inventory_id = int(request.form['inventory_id'])
    from_wh = int(request.form['from_warehouse'])
    to_wh = int(request.form['to_warehouse'])
    qty = float(request.form['quantity'])

    source = InventoryStock.query.filter_by(
        inventory_id=inventory_id,
        warehouse_id=from_wh
    ).first()

    destination = InventoryStock.query.filter_by(
        inventory_id=inventory_id,
        warehouse_id=to_wh
    ).first()

    if source.quantity >= qty:
        source.quantity -= qty

        if not destination:
            destination = InventoryStock(
                inventory_id=inventory_id,
                warehouse_id=to_wh,
                quantity=0
            )
            db.session.add(destination)

        destination.quantity += qty

        db.session.commit()

    return redirect(url_for("inventory_dashboard"))   




@app.route("/iot_update", methods=["POST"])
def iot_update():
    tank_id = request.json['tank_id']
    level = request.json['level']

    tank = IoTTank.query.get(tank_id)
    tank.current_level = level
    tank.last_updated = datetime.utcnow()

    db.session.commit()

    return {"status": "updated"}


@app.route("/delete_inventory/<int:id>")
def delete_inventory(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("inventory"))


# ===================================================
# WEATHER DASHBOARD
# ===================================================

@app.route("/weather")
def weather_dashboard():

    current = WeatherCurrent.query.order_by(
        WeatherCurrent.recorded_at.desc()
    ).first()

    forecast = WeatherForecast.query.all()
    rainfall_logs = RainfallLog.query.all()

    iot_station = IoTWeatherStation.query.order_by(
        IoTWeatherStation.recorded_at.desc()
    ).first()

    soil = SoilMoistureSensor.query.order_by(
        SoilMoistureSensor.recorded_at.desc()
    ).first()

    satellite = SatelliteWeather.query.order_by(
        SatelliteWeather.recorded_at.desc()
    ).first()

    prediction_value = None
    advisory_message = None
    advisory_level = None

    if current and soil:
        prediction_value = ai_yield_estimation(
            current.rainfall_today,
            current.temperature,
            soil.moisture_level
        )

        advisory_message, advisory_level = generate_crop_advisory(
            current.temperature,
            current.humidity,
            current.rainfall_today
        )

    return render_template(
        "weather.html",
        current=current,
        forecast=forecast,
        rainfall_logs=rainfall_logs,
        iot_station=iot_station,
        soil=soil,
        satellite=satellite,
        prediction_value=prediction_value,
        advisory_message=advisory_message,
        advisory_level=advisory_level
    )



@app.route("/add_test_weather")
def add_test_weather():

    weather = WeatherCurrent(
        temperature=32,
        humidity=75,
        rainfall_today=12,
        wind_speed=18,
        cloud_cover=60,
        uv_index=7,
        condition="Cloudy",
        location="Main Farm"
    )

    db.session.add(weather)
    db.session.commit()

    return "Test Weather Added"


@app.route("/add_test_soil")
def add_test_soil():

    soil = SoilMoistureSensor(
        field_name="Field A",
        sensor_id="SM001",
        moisture_level=45,
        soil_temperature=26
    )

    db.session.add(soil)
    db.session.commit()

    return "Soil Data Added"



@app.route("/add_test_satellite")
def add_test_satellite():

    sat = SatelliteWeather(
        location="Main Farm",
        ndvi_index=0.72,
        land_surface_temp=34,
        evapotranspiration=5.2,
        rainfall_estimate=12
    )

    db.session.add(sat)
    db.session.commit()

    return "Satellite Data Added"



@app.route("/add_forecast", methods=["POST"])
def add_forecast():
    forecast = WeatherForecast(
        forecast_date=datetime.strptime(request.form["forecast_date"], "%Y-%m-%d"),
        temperature_min=request.form["temperature_min"],
        temperature_max=request.form["temperature_max"],
        rainfall_prediction=request.form["rainfall_prediction"],
        wind_speed=request.form["wind_speed"],
        storm_warning=True if request.form.get("storm_warning") else False
    )

    db.session.add(forecast)
    db.session.commit()

    return redirect(url_for("weather_dashboard"))


@app.route("/add_rainfall", methods=["POST"])
def add_rainfall():
    rain = RainfallLog(
        date=datetime.strptime(request.form["date"], "%Y-%m-%d"),
        rainfall_mm=request.form["rainfall_mm"],
        location=request.form["location"]
    )

    db.session.add(rain)
    db.session.commit()

    return redirect(url_for("weather_dashboard"))


@app.route("/add_weather", methods=["POST"])
def add_weather():

    new_weather = Weather(
        temperature=request.form.get("temperature"),
        humidity=request.form.get("humidity"),
        rainfall=request.form.get("rainfall"),
        wind_speed=request.form.get("wind_speed"),
        cloud_cover=request.form.get("cloud_cover"),
        uv_index=request.form.get("uv_index")
    )

    db.session.add(new_weather)
    db.session.commit()

    return redirect(url_for("weather_dashboard"))

@app.route("/delete_forecast/<int:id>")
def delete_forecast(id):

    forecast = WeatherForecast.query.get_or_404(id)

    db.session.delete(forecast)
    db.session.commit()

    return redirect(url_for("weather_dashboard"))


@app.route("/loans")
def loan_dashboard():

    loans = Loan.query.all()

    total_active = Loan.query.filter_by(status="Active").count()

    total_outstanding = sum(
        loan.loan_amount for loan in loans if loan.status == "Active"
    )

    total_interest_paid = sum(
        sum(p.late_fee for p in loan.payments)
        for loan in loans
    )

    overdue_loans = LoanEMI.query.filter_by(status="Overdue").count()

    return render_template(
        "loans.html",
        loans=loans,
        total_active=total_active,
        total_outstanding=total_outstanding,
        total_interest_paid=total_interest_paid,
        overdue_loans=overdue_loans
    )



@app.route("/calculate_emi", methods=["POST"])
def calculate_emi():
    P = float(request.form["loan_amount"])
    annual_rate = float(request.form["interest_rate"])
    n = int(request.form["tenure"])

    r = annual_rate / (12 * 100)

    emi = (P * r * (1 + r)**n) / ((1 + r)**n - 1)

    loans = Loan.query.all()

    return render_template(
        "loans.html",
        loans=loans,
        emi_result=round(emi, 2)
    )






@app.route("/loan_analysis", methods=["POST"])
def loan_analysis():
    income = float(request.form["income"])
    total_loan = float(request.form["total_loan"])
    crop_profit = float(request.form["crop_profit"])

    dti = (total_loan / income) * 100 if income > 0 else 0
    burden = (total_loan / crop_profit) * 100 if crop_profit > 0 else 0

    if dti < 30:
        risk = "Low Risk"
    elif dti < 60:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    risk_data = {
        "dti": round(dti, 2),
        "burden": round(burden, 2),
        "risk": risk
    }

    loans = Loan.query.all()

    return render_template(
        "loans.html",
        loans=loans,
        risk_data=risk_data
    )


@app.route("/add_payment", methods=["POST"])
def add_payment():
    loan_id = request.form.get("loan_id")
    amount_paid = float(request.form.get("amount_paid"))

    loan = Loan.query.filter_by(loan_id=loan_id).first()

    if not loan:
        return "Loan not found"

    # Calculate monthly interest
    interest_part = (loan.loan_amount * loan.interest_rate / 100) / 12
    principal_part = amount_paid - interest_part

    if principal_part < 0:
        principal_part = 0

    loan.loan_amount -= principal_part

    if loan.loan_amount <= 0:
        loan.loan_amount = 0
        loan.status = "Closed"

    db.session.commit()

    loans = Loan.query.all()

    return render_template(
        "loans.html",
        loans=loans,
        payment_success=True
    )







@app.route("/loan/<int:loan_id>/impact")
def loan_impact(loan_id):
    loan = Loan.query.get_or_404(loan_id)

    # Example annual income calculation (use your real income logic)
    total_income = sum(i.total_income for i in CropIncome.query.all())

    debt_ratio = (loan.principal_amount / total_income) * 100 if total_income > 0 else 0

    if debt_ratio < 30:
        risk = "Low"
    elif debt_ratio < 60:
        risk = "Medium"
    else:
        risk = "High"

    return render_template(
        "loans_impact.html",
        loan=loan,
        total_income=total_income,
        debt_ratio=debt_ratio,
        risk=risk
    )


@app.route("/loans")
def loans():
    loans_list = Loan.query.all()
    return render_template("loans.html", loans=loans_list)



@app.route("/add_test_loan")
def add_test_loan():
    from datetime import date
    loan = Loan(
        farmer_name="Test Farmer",
        loan_type="Crop Loan",
        principal_amount=100000,
        interest_rate=10,
        tenure_months=12,
        start_date=date.today()
    )
    db.session.add(loan)
    db.session.commit()
    return "Test Loan Added"




@app.route("/reports")
def reports():

    # ================= TOTAL INCOME =================
    crop_income = db.session.query(db.func.sum(CropIncome.net_income)).scalar() or 0
    livestock_income = db.session.query(db.func.sum(LivestockIncome.total_income)).scalar() or 0
    byproduct_income = db.session.query(db.func.sum(ByProductIncome.total_income)).scalar() or 0
    subsidy_income = db.session.query(db.func.sum(GovernmentSubsidy.approved_amount)).scalar() or 0
    insurance_income = db.session.query(db.func.sum(InsuranceClaim.amount_received)).scalar() or 0
    equipment_income = db.session.query(db.func.sum(EquipmentRentalIncome.total_income)).scalar() or 0
    seed_income = db.session.query(db.func.sum(SeedProductionIncome.total_income)).scalar() or 0
    retail_income = db.session.query(db.func.sum(DirectRetailIncome.total_income)).scalar() or 0

    total_income = (
        crop_income +
        livestock_income +
        byproduct_income +
        subsidy_income +
        insurance_income +
        equipment_income +
        seed_income +
        retail_income
    )

    # ================= TOTAL EXPENSE =================
    total_expense = db.session.query(
        db.func.sum(
            Expense.amount + db.func.coalesce(Expense.additional_cost, 0)
        )
    ).scalar() or 0

    net_profit = total_income - total_expense

    # ================= LOAN REPORT =================
    total_loan_outstanding = db.session.query(
        db.func.sum(Loan.loan_amount)
    ).scalar() or 0

    # ================= INVENTORY VALUE =================
    stock_value = db.session.query(
        db.func.sum(InventoryItem.current_stock * InventoryItem.purchase_price)
    ).scalar() or 0

    # ================= WEATHER ANALYSIS =================
    total_rainfall = db.session.query(
    db.func.sum(RainfallLog.rainfall_mm)
).scalar() or 0

    return render_template(
        "reports.html",
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        net_profit=round(net_profit, 2),
        total_loan_outstanding=round(total_loan_outstanding, 2),
        stock_value=round(stock_value, 2),
        total_rainfall=round(total_rainfall, 2)
    )




# ===================================================
# EQUIPMENT + EXPENSE routes remain same as yours
# ===================================================




@app.route("/test")
def test():
 return "Test Route Working"
    


# ALWAYS KEEP THIS LAST
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
