from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
import json
from collections import defaultdict
from functools import wraps
import pymysql
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid

# 加载环境变量
load_dotenv()

pymysql.install_as_MySQLdb()

app = Flask(__name__)

# 从环境变量加载配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('DB_USER', '')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', '')}/{os.getenv('DB_NAME', '')}?charset=utf8mb4&connect_timeout=60&read_timeout=60&write_timeout=60"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 20,
    'pool_recycle': 3600,
    'max_overflow': 20,
    'pool_pre_ping': True
}

# 文件上传配置
app.config['UPLOAD_FOLDER'] = 'static/uploads/suppliers'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    # 检查是否是 AJAX 请求
    # if request.headers.get('Accept') == 'application/json':
    #     # return jsonify({'error': '请先登录才能访问此页面'}), 401
    # # flash('请先登录才能访问此页面', 'error')
    return redirect(url_for('login'))

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    supplier_type = db.Column(db.String(50))  # 保留原字段用于兼容
    supply_categories = db.Column(db.Text)  # 保留原字段用于兼容
    image_path = db.Column(db.String(255))  # 保留原字段用于兼容
    supply_method = db.Column(db.String(50))  # 供应方式：产地直供/合作社、本地批发市场供应商、一件代发供应商、社区本地农户/小农场
    importance_level = db.Column(db.String(50))  # 重要程度：核心供应商、备用供应商、临时供应商
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class SupplierImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    supplier = db.relationship('Supplier', backref='images')

class SupplierSupplyCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    supplier = db.relationship('Supplier', backref='supply_categories_list')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    unit = db.Column(db.String(20))
    stock = db.Column(db.Integer, default=0)  # 库存数量
    description = db.Column(db.Text)  # 商品描述
    image_path = db.Column(db.String(255))  # 商品图片路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    supplier = db.relationship('Supplier', backref='products')

class Receivable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receivable_number = db.Column(db.String(50), unique=True, nullable=False)  # 应收款单号
    title = db.Column(db.String(200), nullable=False)  # 应收款标题/客户名称
    amount = db.Column(db.Float, nullable=False)  # 应收金额
    received_amount = db.Column(db.Float, default=0.0)  # 已收金额
    status = db.Column(db.String(20), default='pending')  # pending, partial, received
    invoice_date = db.Column(db.Date)  # 开票日期
    due_date = db.Column(db.Date)  # 到期日期
    payment_terms = db.Column(db.Integer, default=30)  # 账期天数
    contact_person = db.Column(db.String(100))  # 联系人
    contact_phone = db.Column(db.String(20))  # 联系电话
    contact_address = db.Column(db.String(500))  # 联系地址
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='receivables')
    
    @property
    def remaining_amount(self):
        """计算剩余未收金额"""
        return self.amount - self.received_amount
    
    @property
    def overdue_days(self):
        """计算逾期天数"""
        if not self.due_date or self.status == 'received':
            return 0
        today = datetime.now().date()
        if today > self.due_date:
            return (today - self.due_date).days
        return 0
    
    @property
    def days_until_due(self):
        """计算距离到期的天数"""
        if not self.due_date or self.status == 'received':
            return None
        today = datetime.now().date()
        if today <= self.due_date:
            return (self.due_date - today).days
        return 0

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)
    unit_price = db.Column(db.Float)
    category = db.relationship('Category', backref='transactions')
    supplier = db.relationship('Supplier', backref='transactions')
    product = db.relationship('Product', backref='transactions')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.role in ['admin', 'manager']:
            flash('权限不足', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def edit_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role == 'employee':
            flash('员工权限不足，只能查看数据', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    # 本月收支统计
    month_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        Transaction.date >= month_start
    ).scalar() or 0
    
    month_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        Transaction.date >= month_start
    ).scalar() or 0
    
    # 总体统计数据
    total_transactions = Transaction.query.count()
    total_users = User.query.count()
    total_suppliers = Supplier.query.count()
    total_products = Product.query.count()
    total_categories = Category.query.count()
    
    # 活跃数据统计
    active_suppliers = Supplier.query.filter_by(is_active=True).count()
    active_products = Product.query.filter_by(is_active=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # 总收入支出统计
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'income'
    ).scalar() or 0
    
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense'
    ).scalar() or 0
    
    # 最近交易
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()
    
    # 分类统计
    category_stats = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        Transaction.date >= month_start
    ).group_by(Category.name).all()
    
    # 供应商统计
    supplier_stats = db.session.query(
        Supplier.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        Transaction.date >= month_start
    ).group_by(Supplier.name).limit(5).all()
    
    # 应收款统计
    receivables_list = Receivable.query.filter_by(user_id=current_user.id).all()
    total_receivables = sum(r.amount for r in receivables_list)
    received_receivables = sum(r.amount for r in receivables_list if r.status == 'received')
    pending_receivables = total_receivables - received_receivables
    
    # 计算现金余额（总收入 - 总支出）
    cash_balance = total_income - total_expense
    
    # 获取过去12个月的收支数据用于趋势图
    trend_data = []
    for i in range(12):
        month_date = (today.replace(day=1) - timedelta(days=32*i)).replace(day=1)
        next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        month_income_trend = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.date >= month_date,
            Transaction.date < next_month
        ).scalar() or 0
        
        month_expense_trend = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.date >= month_date,
            Transaction.date < next_month
        ).scalar() or 0
        
        trend_data.insert(0, {
            'month': month_date.strftime('%m月'),
            'income': float(month_income_trend),
            'expense': float(month_expense_trend)
        })
    
    # 获取收入分类数据用于饼图
    income_category_stats = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'income',
        Transaction.date >= month_start
    ).group_by(Category.name).all()
    
    # 获取支出分类数据用于饼图
    expense_category_stats = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        Transaction.date >= month_start
    ).group_by(Category.name).all()
    
    # 本年收支统计
    year_start = today.replace(month=1, day=1)
    year_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        Transaction.date >= year_start
    ).scalar() or 0
    
    year_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        Transaction.date >= year_start
    ).scalar() or 0
    
    # 获取年度收入分类数据用于饼图
    year_income_category_stats = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'income',
        Transaction.date >= year_start
    ).group_by(Category.name).all()
    
    # 获取年度支出分类数据用于饼图
    year_expense_category_stats = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        Transaction.date >= year_start
    ).group_by(Category.name).all()
    
    # 获取年度数据用于趋势图
    current_year = today.year
    year_data = []
    
    # 获取过去6年的数据
    for year_offset in range(5, -1, -1):
        target_year = current_year - year_offset
        year_start_trend = datetime(target_year, 1, 1)
        year_end_trend = datetime(target_year + 1, 1, 1)
        
        year_income_trend = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.date >= year_start_trend,
            Transaction.date < year_end_trend
        ).scalar() or 0
        
        year_expense_trend = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.date >= year_start_trend,
            Transaction.date < year_end_trend
        ).scalar() or 0
        
        year_data.append({
            'year': str(target_year),
            'income': float(year_income_trend),
            'expense': float(year_expense_trend)
        })
    
    return render_template('dashboard.html', 
                         month_income=month_income,
                         month_expense=month_expense,
                         year_income=year_income,
                         year_expense=year_expense,
                         recent_transactions=recent_transactions,
                         category_stats=category_stats,
                         supplier_stats=supplier_stats,
                         total_transactions=total_transactions,
                         total_users=total_users,
                         total_suppliers=total_suppliers,
                         total_products=total_products,
                         total_categories=total_categories,
                         active_suppliers=active_suppliers,
                         active_products=active_products,
                         active_users=active_users,
                         total_income=total_income,
                         total_expense=total_expense,
                         total_receivables=total_receivables,
                         received_receivables=received_receivables,
                         pending_receivables=pending_receivables,
                         cash_balance=cash_balance,
                         trend_data=trend_data,
                         year_data=year_data,
                         income_category_stats=income_category_stats,
                         expense_category_stats=expense_category_stats,
                         year_income_category_stats=year_income_category_stats,
                         year_expense_category_stats=year_expense_category_stats)

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    
    # 获取筛选参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type')
    category_id = request.args.get('category_id')
    
    # 构建查询
    query = Transaction.query
    
    # 日期范围筛选
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Transaction.date >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # 包含结束日期的整天
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Transaction.date <= end_date_obj)
        except ValueError:
            pass
    
    # 交易类型筛选
    if transaction_type and transaction_type in ['income', 'expense']:
        query = query.filter(Transaction.type == transaction_type)
    
    # 分类筛选
    if category_id:
        try:
            category_id_int = int(category_id)
            query = query.filter(Transaction.category_id == category_id_int)
        except ValueError:
            pass
    
    # 排序和分页
    transactions = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    categories = Category.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    # 传递当前筛选参数到模板
    filter_params = {
        'start_date': start_date,
        'end_date': end_date,
        'type': transaction_type,
        'category_id': category_id
    }
    
    return render_template('transactions.html', 
                         transactions=transactions, 
                         categories=categories, 
                         suppliers=suppliers, 
                         products=products,
                         filter_params=filter_params)

@app.route('/add_transaction', methods=['GET', 'POST'])
@edit_required
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        transaction_type = request.form['type']
        description = request.form['description']
        category_id = int(request.form['category'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        
        supplier_id = request.form.get('supplier') or None
        product_id = request.form.get('product') or None
        quantity = request.form.get('quantity') or None
        unit_price = request.form.get('unit_price') or None
        
        if supplier_id:
            supplier_id = int(supplier_id)
        if product_id:
            product_id = int(product_id)
        if quantity:
            quantity = float(quantity)
        if unit_price:
            unit_price = float(unit_price)
        
        transaction = Transaction(
            amount=amount,
            type=transaction_type,
            description=description,
            category_id=category_id,
            user_id=current_user.id,
            date=date,
            supplier_id=supplier_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        db.session.add(transaction)
        db.session.commit()
        flash('交易记录添加成功！', 'success')
        return redirect(url_for('transactions'))
    
    # 获取所有分类，让前端JavaScript根据类型过滤
    transaction_type = request.args.get('type', 'expense')
    categories = Category.query.all()
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_transaction.html', categories=categories, suppliers=suppliers, products=products, today=today, transaction_type=transaction_type)

@app.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
@edit_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    if request.method == 'POST':
        transaction.amount = float(request.form['amount'])
        transaction.type = request.form['type']
        transaction.description = request.form['description']
        transaction.category_id = int(request.form['category'])
        transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        
        supplier_id = request.form.get('supplier') or None
        product_id = request.form.get('product') or None
        quantity = request.form.get('quantity') or None
        unit_price = request.form.get('unit_price') or None
        
        if supplier_id:
            supplier_id = int(supplier_id)
        if product_id:
            product_id = int(product_id)
        if quantity:
            quantity = float(quantity)
        if unit_price:
            unit_price = float(unit_price)
        
        transaction.supplier_id = supplier_id
        transaction.product_id = product_id
        transaction.quantity = quantity
        transaction.unit_price = unit_price
        
        db.session.commit()
        flash('交易记录更新成功！', 'success')
        return redirect(url_for('transactions'))
    
    categories = Category.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    return render_template('edit_transaction.html', transaction=transaction, categories=categories, suppliers=suppliers, products=products)

@app.route('/delete_transaction/<int:id>')
@edit_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    db.session.delete(transaction)
    db.session.commit()
    flash('交易记录删除成功！', 'success')
    
    return redirect(url_for('transactions'))

@app.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/add_category', methods=['GET', 'POST'])
@edit_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        category_type = request.form['type']
        color = request.form['color']
        
        category = Category(
            name=name,
            type=category_type,
            color=color,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功！', 'success')
        return redirect(url_for('categories'))
    
    return render_template('add_category.html')

@app.route('/edit_category/<int:id>', methods=['GET', 'POST'])
@edit_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.type = request.form['type']
        category.color = request.form['color']
        
        db.session.commit()
        flash('分类更新成功！', 'success')
        return redirect(url_for('categories'))
    
    return render_template('edit_category.html', category=category)

@app.route('/delete_category/<int:id>')
@edit_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # 检查是否有关联的交易
    if category.transactions:
        flash('无法删除：该分类下有关联的交易记录', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类删除成功！', 'success')
    
    return redirect(url_for('categories'))

@app.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/supplier/<int:id>')
@login_required
def supplier_detail(id):
    supplier = Supplier.query.get_or_404(id)
    return render_template('supplier_detail.html', supplier=supplier)

@app.route('/add_supplier', methods=['GET', 'POST'])
@edit_required
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        address = request.form['address']
        supply_method = request.form.get('supply_method', '')
        importance_level = request.form.get('importance_level', '')
        supply_categories = request.form.getlist('supply_categories')  # 获取多个品类
        
        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            phone=phone,
            address=address,
            supply_method=supply_method,
            importance_level=importance_level
        )
        db.session.add(supplier)
        db.session.flush()  # 获取supplier.id
        
        # 添加供货品类
        for category in supply_categories:
            if category.strip():
                supply_category = SupplierSupplyCategory(
                    supplier_id=supplier.id,
                    product_name=category.strip()
                )
                db.session.add(supply_category)
        
        # 处理图片上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    supplier_image = SupplierImage(
                        supplier_id=supplier.id,
                        image_path=f"static/uploads/suppliers/{unique_filename}"
                    )
                    db.session.add(supplier_image)
        
        db.session.commit()
        flash('供应商添加成功！', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('add_supplier.html')

@app.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
@edit_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        supplier.name = request.form['name']
        supplier.contact_person = request.form['contact_person']
        supplier.phone = request.form['phone']
        supplier.address = request.form['address']
        supplier.supply_method = request.form.get('supply_method', '')
        supplier.importance_level = request.form.get('importance_level', '')
        supplier.is_active = 'is_active' in request.form
        
        # 更新供货品类
        new_categories = request.form.getlist('supply_categories')
        # 删除旧的品类
        SupplierSupplyCategory.query.filter_by(supplier_id=supplier.id).delete()
        # 添加新的品类
        for category in new_categories:
            if category.strip():
                supply_category = SupplierSupplyCategory(
                    supplier_id=supplier.id,
                    product_name=category.strip()
                )
                db.session.add(supply_category)
        
        # 处理图片上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    supplier_image = SupplierImage(
                        supplier_id=supplier.id,
                        image_path=f"static/uploads/suppliers/{unique_filename}"
                    )
                    db.session.add(supplier_image)
        
        db.session.commit()
        flash('供应商更新成功！', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('edit_supplier.html', supplier=supplier)

@app.route('/delete_supplier/<int:id>')
@edit_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    
    # 检查是否有关联的交易或商品
    if supplier.transactions or supplier.products:
        flash('无法删除：该供应商下有关联的交易记录或商品', 'error')
    else:
        # 删除供应商图片
        for image in supplier.images:
            # image.image_path 已经包含了 static/uploads/suppliers/ 前缀
            if os.path.exists(image.image_path):
                os.remove(image.image_path)
            # 同时删除数据库中的图片记录
            db.session.delete(image)
        
        db.session.delete(supplier)
        db.session.commit()
        flash('供应商删除成功！', 'success')
    
    return redirect(url_for('suppliers'))

@app.route('/api/products')
@login_required
def api_products():
    """获取所有商品名称，用于供货品类选择"""
    products = Product.query.filter_by(is_active=True).all()
    product_names = [product.name for product in products]
    return jsonify(product_names)

@app.route('/api/product/<int:id>')
@login_required
def api_product_detail(id):
    """获取单个商品的详细信息"""
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'code': f'PRD{product.id:03d}',  # 生成商品编号
        'category': product.category,
        'category_id': product.category,  # 暂时使用category字段
        'supplier_id': product.supplier_id,
        'cost': product.cost_price,
        'cost_price': product.cost_price,
        'price': product.selling_price,  # 前端使用price字段
        'selling_price': product.selling_price,
        'unit': product.unit,
        'stock': product.stock or 0,
        'min_stock': 10,  # 默认最低库存
        'max_stock': 1000,  # 默认最高库存
        'description': product.description or '',
        'image_path': product.image_path,
        'is_active': product.is_active,
        'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else None
    })

@app.route('/api/product/<int:id>/stock', methods=['POST'])
@edit_required
def api_product_stock_operation(id):
    """商品库存操作"""
    product = Product.query.get_or_404(id)
    data = request.get_json()
    
    operation_type = data.get('operation_type')
    quantity = data.get('quantity', 0)
    remark = data.get('remark', '')
    
    try:
        if operation_type == 'in':
            # 入库
            product.stock += quantity
        elif operation_type == 'out':
            # 出库
            if product.stock < quantity:
                return jsonify({'success': False, 'message': '库存不足，无法出库'}), 400
            product.stock -= quantity
        elif operation_type == 'adjust':
            # 调整
            product.stock = quantity
        else:
            return jsonify({'success': False, 'message': '无效的操作类型'}), 400
        
        # 记录库存变动（这里可以添加库存变动记录表）
        # 暂时只更新商品库存
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '库存操作成功',
            'new_stock': product.stock
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@app.route('/api/supplier/<int:id>')
@login_required
def api_supplier_detail(id):
    """获取单个供应商的详细信息"""
    supplier = Supplier.query.get_or_404(id)
    return jsonify({
        'id': supplier.id,
        'name': supplier.name,
        'contact_person': supplier.contact_person,
        'phone': supplier.phone,
        'email': supplier.email,
        'address': supplier.address,
        'supplier_type': supplier.supplier_type,
        'supply_categories': supplier.supply_categories,
        'supply_method': supplier.supply_method,
        'importance_level': supplier.importance_level,
        'is_active': supplier.is_active,
        'created_at': supplier.created_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.created_at else None
    })

@app.route('/api/supplier/<int:id>', methods=['PUT'])
@edit_required
def api_update_supplier(id):
    """更新供应商信息"""
    supplier = Supplier.query.get_or_404(id)
    data = request.get_json()
    
    try:
        supplier.name = data.get('name', supplier.name)
        supplier.contact_person = data.get('contact_person', supplier.contact_person)
        supplier.phone = data.get('phone', supplier.phone)
        supplier.email = data.get('email', supplier.email)
        supplier.address = data.get('address', supplier.address)
        supplier.is_active = data.get('is_active', supplier.is_active)
        
        db.session.commit()
        return jsonify({'message': '供应商更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'更新失败: {str(e)}'}), 500

@app.route('/api/supplier', methods=['POST'])
@edit_required
def api_create_supplier():
    """创建新供应商"""
    data = request.get_json()
    
    try:
        supplier = Supplier(
            name=data.get('name'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(supplier)
        db.session.commit()
        return jsonify({'message': '供应商创建成功', 'id': supplier.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'创建失败: {str(e)}'}), 500

@app.route('/api/supplier/<int:id>/images')
@login_required
def api_supplier_images(id):
    """获取供应商的所有图片"""
    supplier = Supplier.query.get_or_404(id)
    images = [{'id': img.id, 'path': img.image_path, 'upload_time': img.upload_time.strftime('%Y-%m-%d %H:%M:%S')} for img in supplier.images]
    return jsonify(images)

@app.route('/api/supplier/<int:id>/images', methods=['POST'])
@edit_required
def api_upload_supplier_image(id):
    """上传供应商图片"""
    supplier = Supplier.query.get_or_404(id)
    
    # 支持单个文件上传（image字段）和多个文件上传（images字段）
    files = []
    if 'images' in request.files:
        files = request.files.getlist('images')
    elif 'image' in request.files:
        files = [request.files['image']]
    
    if not files:
        return jsonify({'error': '没有选择文件'}), 400
    
    uploaded_images = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            image_path = f"static/uploads/suppliers/{unique_filename}"
            supplier_image = SupplierImage(supplier_id=supplier.id, image_path=image_path)
            db.session.add(supplier_image)
            db.session.commit()
            
            uploaded_images.append({
                'id': supplier_image.id,
                'path': supplier_image.image_path,
                'upload_time': supplier_image.upload_time.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    if uploaded_images:
        return jsonify({
            'success': True,
            'images': uploaded_images
        })
    else:
        return jsonify({'error': '没有有效的图片文件或不支持的文件格式'}), 400

@app.route('/api/supplier/<int:supplier_id>/images/<int:image_id>', methods=['DELETE'])
@edit_required
def api_delete_supplier_image(supplier_id, image_id):
    """删除供应商图片"""
    supplier_image = SupplierImage.query.get_or_404(image_id)
    
    if supplier_image.supplier_id != supplier_id:
        return jsonify({'error': '图片不属于该供应商'}), 400
    
    # 删除文件
    image_path = os.path.join('static', supplier_image.image_path)
    if os.path.exists(image_path):
        os.remove(image_path)
    
    db.session.delete(supplier_image)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    return render_template('products.html', products=products, suppliers=suppliers, categories=categories)

@app.route('/add_product', methods=['GET', 'POST'])
@edit_required
def add_product():
    if request.method == 'POST':
        # 检查是否为AJAX请求
        is_ajax = 'X-Requested-With' in request.headers and request.headers['X-Requested-With'] == 'XMLHttpRequest'
        
        name = request.form['name']
        category = request.form.get('category')
        supplier_id = int(request.form['supplier']) if request.form.get('supplier') else None
        cost_price = float(request.form['cost_price']) if request.form.get('cost_price') else None
        selling_price = float(request.form['selling_price']) if request.form.get('selling_price') else None
        unit = request.form.get('unit', '件')
        description = request.form.get('description', '')
        is_active = request.form.get('is_active', '1') == '1'
        
        # 检查商品名称是否已存在
        if Product.query.filter_by(name=name).first():
            if is_ajax:
                return jsonify({'success': False, 'message': '商品名称已存在'}), 400
            flash('商品名称已存在', 'error')
            suppliers = Supplier.query.filter_by(is_active=True).all()
            return render_template('add_product.html', suppliers=suppliers)
        
        # 处理图片上传
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # 创建商品图片上传目录
                product_upload_folder = 'static/uploads/products'
                os.makedirs(product_upload_folder, exist_ok=True)
                
                # 生成唯一文件名
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(product_upload_folder, unique_filename)
                
                try:
                    file.save(file_path)
                    image_path = f"uploads/products/{unique_filename}"
                except Exception as e:
                    if is_ajax:
                        return jsonify({'success': False, 'message': f'图片上传失败: {str(e)}'}), 500
                    flash(f'图片上传失败: {str(e)}', 'error')
                    suppliers = Supplier.query.filter_by(is_active=True).all()
                    return render_template('add_product.html', suppliers=suppliers)
        
        product = Product(
            name=name,
            category=category,
            supplier_id=supplier_id,
            cost_price=cost_price,
            selling_price=selling_price,
            unit=unit,
            description=description,
            image_path=image_path,
            is_active=is_active
        )
        db.session.add(product)
        db.session.commit()
        
        if is_ajax:
            return jsonify({'success': True})
        
        flash('商品添加成功！', 'success')
        return redirect(url_for('products'))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    categories = Category.query.all()  # 添加分类数据
    return render_template('add_product.html', suppliers=suppliers, categories=categories)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@edit_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # 更新基本信息
            product.name = request.form['name']
            product.category = request.form['category']
            product.supplier_id = int(request.form['supplier']) if request.form.get('supplier') else None
            product.cost_price = float(request.form['cost_price']) if request.form['cost_price'] else None
            product.selling_price = float(request.form['selling_price']) if request.form['selling_price'] else None
            product.unit = request.form['unit']
            product.stock = int(request.form['stock']) if request.form['stock'] else 0
            product.description = request.form['description']
            product.is_active = request.form.get('is_active') == '1'
            
            # 检查是否需要删除图片
            remove_image = request.form.get('remove_image') == '1'
            print(f"Debug: remove_image = {remove_image}, product.image_path = {product.image_path}")
            if remove_image and product.image_path:
                # 删除旧图片文件
                old_image_path = os.path.join('static', product.image_path.lstrip('/'))
                print(f"Debug: 尝试删除图片文件: {old_image_path}")
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                    print(f"Debug: 成功删除图片文件: {old_image_path}")
                else:
                    print(f"Debug: 图片文件不存在: {old_image_path}")
                # 清空数据库中的图片路径
                product.image_path = None
                print(f"Debug: 已清空数据库中的图片路径")
            
            # 处理图片上传
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    # 删除旧图片（如果存在且未被上面的删除逻辑处理）
                    if product.image_path and not remove_image:
                        old_image_path = os.path.join('static', product.image_path.lstrip('/'))
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # 保存新图片
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # 确保商品图片目录存在
                    product_upload_folder = 'static/uploads/products'
                    os.makedirs(product_upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(product_upload_folder, unique_filename)
                    file.save(file_path)
                    product.image_path = f'uploads/products/{unique_filename}'
            
            db.session.commit()
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})
            else:
                flash('商品信息更新成功！', 'success')
                return redirect(url_for('products'))
                
        except Exception as e:
            db.session.rollback()
            error_message = f'更新失败：{str(e)}'
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_message})
            else:
                flash(error_message, 'error')
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('edit_product.html', product=product, suppliers=suppliers)

@app.route('/delete_product/<int:id>')
@edit_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # 检查是否为AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 检查是否有关联的交易
        if product.transactions:
            return jsonify({'success': False, 'message': '无法删除：该商品下有关联的交易记录'})
        else:
            try:
                db.session.delete(product)
                db.session.commit()
                return jsonify({'success': True, 'message': '商品删除成功！'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})
    else:
        # 非AJAX请求，保持原有逻辑
        if product.transactions:
            flash('无法删除：该商品下有关联的交易记录', 'error')
        else:
            db.session.delete(product)
            db.session.commit()
            flash('商品删除成功！', 'success')
        
        return redirect(url_for('products'))

@app.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        # 检查是否为AJAX请求
        is_ajax = request.headers.get('Content-Type') == 'multipart/form-data' or request.is_json or 'XMLHttpRequest' in request.headers.get('X-Requested-With', '')
        
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        is_active = request.form.get('is_active', '1') == '1'
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            if is_ajax:
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            flash('用户名已存在', 'error')
            return render_template('add_user.html')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            if is_ajax:
                return jsonify({'success': False, 'message': '邮箱已存在'}), 400
            flash('邮箱已存在', 'error')
            return render_template('add_user.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_active=is_active
        )
        db.session.add(user)
        db.session.commit()
        
        if is_ajax:
            return jsonify({'success': True, 'message': '用户添加成功！'})
        
        flash('用户添加成功！', 'success')
        return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # 检查是否为AJAX请求
        is_ajax = request.headers.get('Content-Type') == 'multipart/form-data' or request.is_json or 'XMLHttpRequest' in request.headers.get('X-Requested-With', '')
        
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        is_active = 'is_active' in request.form
        
        # 检查用户名是否已存在（排除当前用户）
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            if is_ajax:
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            flash('用户名已存在', 'error')
            return render_template('edit_user.html', user=user)
        
        # 检查邮箱是否已存在（排除当前用户）
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            if is_ajax:
                return jsonify({'success': False, 'message': '邮箱已存在'}), 400
            flash('邮箱已存在', 'error')
            return render_template('edit_user.html', user=user)
        
        user.username = username
        user.email = email
        user.role = role
        user.is_active = is_active
        
        # 如果提供了新密码，则更新密码
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        
        if is_ajax:
            return jsonify({'success': True, 'message': '用户更新成功！'})
        
        flash('用户更新成功！', 'success')
        return redirect(url_for('users'))
    
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:id>')
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账户', 'error')
        return redirect(url_for('users'))
    
    # 不能删除最后一个管理员
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            flash('不能删除最后一个管理员账户', 'error')
            return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功！', 'success')
    
    return redirect(url_for('users'))

@app.route('/statistics')
@login_required
def statistics():
    """财务分析页面 - 重新设计的简洁版本"""
    try:
        # 获取当前日期
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        # 基础财务数据
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'income'
        ).scalar() or 0
        
        total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense'
        ).scalar() or 0
        
        net_assets = total_income - total_expense
        liability_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
        
        # 财务健康度评分（简化版）
        if net_assets > 0:
            health_score = min(100, max(0, int(100 - liability_ratio)))
        else:
            health_score = 0
        
        # 获取最近6个月的趋势数据
        six_months_ago = datetime.now() - timedelta(days=180)
        
        monthly_stats = db.session.query(
            db.func.date_format(Transaction.date, '%Y-%m').label('month'),
            Transaction.type,
            db.func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.date >= six_months_ago
        ).group_by(
            db.func.date_format(Transaction.date, '%Y-%m'),
            Transaction.type
        ).order_by('month').all()
        
        # 处理趋势数据
        month_data = defaultdict(lambda: {'income': 0, 'expense': 0})
        for stat in monthly_stats:
            month_data[stat.month][stat.type] = stat.total
        
        trend_months = []
        trend_income = []
        trend_expense = []
        trend_profit = []
        monthly_data = []
        
        for month in sorted(month_data.keys()):
            income = month_data[month]['income']
            expense = month_data[month]['expense']
            profit = income - expense
            
            trend_months.append(month)
            trend_income.append(income)
            trend_expense.append(expense)
            trend_profit.append(profit)
            
            monthly_data.append({
                'date': month,
                'income': income,
                'expense': expense,
                'profit': profit,
                'mom_growth': 0,  # 简化版暂不计算增长率
                'yoy_growth': 0
            })
        
        # 收支分类数据
        income_categories = db.session.query(
            Category.name,
            db.func.sum(Transaction.amount).label('amount')
        ).join(Transaction).filter(
            Transaction.type == 'income',
            Transaction.date >= six_months_ago
        ).group_by(Category.name).all()
        
        expense_categories = db.session.query(
            Category.name,
            db.func.sum(Transaction.amount).label('amount')
        ).join(Transaction).filter(
            Transaction.type == 'expense',
            Transaction.date >= six_months_ago
        ).group_by(Category.name).all()
        
        # 饼图数据
        income_colors = ['#57B5E7', '#8DD3C7', '#9333EA', '#FB923C', '#F59E0B']
        expense_colors = ['#FBBF72', '#FC8D62', '#EAB308', '#EF4444', '#8B5CF6']
        
        income_pie_data = [
            {
                'value': cat.amount, 
                'name': cat.name, 
                'itemStyle': {'color': income_colors[i % len(income_colors)]}
            }
            for i, cat in enumerate(income_categories)
        ]
        
        expense_pie_data = [
            {
                'value': cat.amount, 
                'name': cat.name, 
                'itemStyle': {'color': expense_colors[i % len(expense_colors)]}
            }
            for i, cat in enumerate(expense_categories)
        ]
        
        # 现金流瀑布图数据（简化版）
        # 本月数据
        current_month_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.date >= month_start,
            Transaction.date <= today
        ).scalar() or 0
        
        current_month_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date <= today
        ).scalar() or 0
        
        # 上月结余（简化计算）
        last_month_end = month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        last_month_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.date >= last_month_start,
            Transaction.date <= last_month_end
        ).scalar() or 0
        
        last_month_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.date >= last_month_start,
            Transaction.date <= last_month_end
        ).scalar() or 0
        
        initial_cash = last_month_income - last_month_expense
        operating_cash = current_month_income
        investing_cash = -current_month_expense * 0.3  # 假设30%为投资支出
        financing_cash = -current_month_expense * 0.7  # 假设70%为运营支出
        final_cash = initial_cash + operating_cash + investing_cash + financing_cash
        
        cashflow_data = [
            {'value': float(initial_cash), 'itemStyle': {'color': '#57B5E7'}},
            {'value': float(operating_cash), 'itemStyle': {'color': '#8DD3C7'}},
            {'value': float(investing_cash), 'itemStyle': {'color': '#FC8D62'}},
            {'value': float(financing_cash), 'itemStyle': {'color': '#FBBF72'}},
            {'value': float(final_cash), 'itemStyle': {'color': '#57B5E7'}}
        ]
        
        # 增长率数据（简化版）
        assets_growth = 0
        liabilities_growth = 0
        net_assets_growth = 0
        liability_ratio_change = 0
        
        return render_template('statistics.html',
                             total_assets=total_income,
                             total_liabilities=total_expense,
                             net_assets=net_assets,
                             liability_ratio=liability_ratio,
                             health_score=health_score,
                             trend_months=trend_months,
                             trend_income=trend_income,
                             trend_expense=trend_expense,
                             trend_profit=trend_profit,
                             income_categories=income_categories,
                             expense_categories=expense_categories,
                             income_pie_data=income_pie_data,
                             expense_pie_data=expense_pie_data,
                             cashflow_data=cashflow_data,
                             monthly_data=monthly_data,
                             assets_growth=assets_growth,
                             liabilities_growth=liabilities_growth,
                             net_assets_growth=net_assets_growth,
                             liability_ratio_change=liability_ratio_change)
    
    except Exception as e:
        flash(f'财务分析数据加载失败: {str(e)}', 'error')
        return render_template('statistics.html',
                             total_assets=0,
                             total_liabilities=0,
                             net_assets=0,
                             liability_ratio=0,
                             health_score=0,
                             trend_months=[],
                             trend_income=[],
                             trend_expense=[],
                             trend_profit=[],
                             income_categories=[],
                             expense_categories=[],
                             income_pie_data=[],
                             expense_pie_data=[],
                             cashflow_data=[],
                             monthly_data=[],
                             assets_growth=0,
                             liabilities_growth=0,
                             net_assets_growth=0,
                             liability_ratio_change=0)

@app.route('/receivables')
@login_required
def receivables():
    # 显示所有应收款记录，而不是只显示当前用户的
    receivables_list = Receivable.query.order_by(Receivable.created_at.desc()).all()
    
    # 计算统计数据
    total_amount = sum(r.amount for r in receivables_list)
    received_amount = sum(r.received_amount for r in receivables_list)
    pending_amount = total_amount - received_amount
    
    # 计算逾期金额
    overdue_amount = sum(r.remaining_amount for r in receivables_list if r.overdue_days > 0)
    
    total_count = len(receivables_list)
    
    return render_template('receivables.html', 
                         receivables=receivables_list,
                         total_amount=total_amount,
                         received_amount=received_amount,
                         pending_amount=pending_amount,
                         overdue_amount=overdue_amount,
                         total_count=total_count)

@app.route('/receivables/add', methods=['GET', 'POST'])
@edit_required
def add_receivable():
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        invoice_date_str = request.form.get('invoice_date')
        due_date_str = request.form.get('due_date')
        payment_terms = int(request.form.get('payment_terms', 30))
        contact_person = request.form.get('contact_person', '')
        contact_phone = request.form.get('contact_phone', '')
        contact_address = request.form.get('contact_address', '')
        notes = request.form.get('notes', '')
        
        # 生成应收款单号
        today = datetime.now()
        receivable_number = f"AR{today.strftime('%Y%m%d')}{str(Receivable.query.count() + 1).zfill(3)}"
        
        # 处理日期
        invoice_date = None
        due_date = None
        
        if invoice_date_str:
            try:
                invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                # 如果没有指定到期日期但有开票日期，则根据账期计算
                if invoice_date:
                    due_date = invoice_date + timedelta(days=payment_terms)
        elif invoice_date:
            # 如果只有开票日期，根据账期计算到期日期
            due_date = invoice_date + timedelta(days=payment_terms)
        
        receivable = Receivable(
            receivable_number=receivable_number,
            title=title,
            amount=amount,
            invoice_date=invoice_date,
            due_date=due_date,
            payment_terms=payment_terms,
            contact_person=contact_person,
            contact_phone=contact_phone,
            contact_address=contact_address,
            notes=notes,
            user_id=current_user.id
        )
        
        db.session.add(receivable)
        db.session.commit()
        flash('应收款添加成功', 'success')
        return redirect(url_for('receivables'))
    
    return render_template('add_receivable.html')

@app.route('/receivables/<int:id>/receive', methods=['POST'])
@edit_required
def receive_receivable(id):
    receivable = Receivable.query.get_or_404(id)
    if receivable:
        received_amount = float(request.form.get('received_amount', 0))
        if received_amount > 0:
            receivable.received_amount += received_amount
            
            # 更新状态
            if receivable.received_amount >= receivable.amount:
                receivable.status = 'received'
                receivable.received_at = datetime.utcnow()
            else:
                receivable.status = 'partial'
            
            db.session.commit()
            flash(f'收款记录已更新，收款金额：¥{received_amount:.2f}', 'success')
        else:
            flash('收款金额必须大于0', 'error')
    else:
        flash('应收款不存在', 'error')
    
    return redirect(url_for('receivables'))

@app.route('/receivables/<int:id>/mark_received')
@edit_required
def mark_received(id):
    """快速标记为已收款"""
    receivable = Receivable.query.get_or_404(id)
    if receivable:
        receivable.received_amount = receivable.amount
        receivable.status = 'received'
        receivable.received_at = datetime.utcnow()
        db.session.commit()
        flash('应收款已标记为已收', 'success')
    else:
        flash('应收款不存在', 'error')
    
    return redirect(url_for('receivables'))

@app.route('/receivables/<int:id>/delete')
@edit_required
def delete_receivable(id):
    receivable = Receivable.query.get_or_404(id)
    if receivable:
        db.session.delete(receivable)
        db.session.commit()
        flash('应收款已删除', 'success')
    else:
        flash('应收款不存在', 'error')
    
    return redirect(url_for('receivables'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/settings')
@admin_required
def settings():
    return render_template('settings.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 仅在直接运行app.py时启动开发服务器（用于开发调试）
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("数据库表创建成功")

            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@company.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("默认管理员账户已创建 - 用户名: admin, 密码: admin123")
            else:
                print("管理员账户已存在")
                
        except Exception as e:
            print(f"数据库连接或初始化失败: {e}")
            print("请检查MySQL连接配置和数据库是否存在")
            exit(1)
    
    print("\n注意: 当前使用Flask开发服务器")
    print("生产环境请使用: python wsgi.py 或 start_wsgi.bat")
    print("="*50)
    app.run(host='0.0.0.0', port=5085, debug=True)