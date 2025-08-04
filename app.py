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

pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://mysql:12345678@acbim.fun/MoneyMind'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    flash('请先登录才能访问此页面', 'error')
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    unit = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    supplier = db.relationship('Supplier', backref='products')

class Receivable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, received
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='receivables')

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
    
    return render_template('dashboard.html', 
                         month_income=month_income,
                         month_expense=month_expense,
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
                         pending_receivables=pending_receivables)

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    categories = Category.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    return render_template('transactions.html', transactions=transactions, categories=categories, suppliers=suppliers, products=products)

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
    
    categories = Category.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_transaction.html', categories=categories, suppliers=suppliers, products=products, today=today)

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

@app.route('/add_supplier', methods=['GET', 'POST'])
@edit_required
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address
        )
        db.session.add(supplier)
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
        supplier.email = request.form['email']
        supplier.address = request.form['address']
        supplier.is_active = 'is_active' in request.form
        
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
        db.session.delete(supplier)
        db.session.commit()
        flash('供应商删除成功！', 'success')
    
    return redirect(url_for('suppliers'))

@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('products.html', products=products, suppliers=suppliers)

@app.route('/add_product', methods=['GET', 'POST'])
@edit_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        supplier_id = int(request.form['supplier']) if request.form['supplier'] else None
        cost_price = float(request.form['cost_price']) if request.form['cost_price'] else None
        selling_price = float(request.form['selling_price']) if request.form['selling_price'] else None
        unit = request.form['unit']
        
        product = Product(
            name=name,
            category=category,
            supplier_id=supplier_id,
            cost_price=cost_price,
            selling_price=selling_price,
            unit=unit
        )
        db.session.add(product)
        db.session.commit()
        flash('商品添加成功！', 'success')
        return redirect(url_for('products'))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('add_product.html', suppliers=suppliers)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@edit_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.category = request.form['category']
        product.supplier_id = int(request.form['supplier']) if request.form['supplier'] else None
        product.cost_price = float(request.form['cost_price']) if request.form['cost_price'] else None
        product.selling_price = float(request.form['selling_price']) if request.form['selling_price'] else None
        product.unit = request.form['unit']
        product.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('商品更新成功！', 'success')
        return redirect(url_for('products'))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('edit_product.html', product=product, suppliers=suppliers)

@app.route('/delete_product/<int:id>')
@edit_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # 检查是否有关联的交易
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('add_user.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        flash('用户添加成功！', 'success')
        return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/statistics')
@login_required
def statistics():
    days = request.args.get('days', 30, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    if transactions:
        income_by_date = defaultdict(float)
        expense_by_date = defaultdict(float)
        
        for transaction in transactions:
            date_str = transaction.date.strftime('%Y-%m-%d')
            if transaction.type == 'income':
                income_by_date[date_str] += transaction.amount
            else:
                expense_by_date[date_str] += transaction.amount
        
        all_dates = sorted(set(list(income_by_date.keys()) + list(expense_by_date.keys())))
        income_data = [income_by_date.get(date, 0) for date in all_dates]
        expense_data = [expense_by_date.get(date, 0) for date in all_dates]
        
        fig = go.Figure()
        
        # 添加收入柱形图
        fig.add_trace(go.Bar(
            x=all_dates, 
            y=income_data, 
            name='收入', 
            marker_color='green',
            opacity=0.8
        ))
        
        # 添加支出柱形图
        fig.add_trace(go.Bar(
            x=all_dates, 
            y=expense_data, 
            name='支出', 
            marker_color='red',
            opacity=0.8
        ))
        
        # 更新布局
        fig.update_layout(
            title='收支趋势图',
            xaxis_title='日期',
            yaxis_title='金额 (元)',
            barmode='group',  # 分组显示柱形图
            xaxis=dict(
                type='category',  # 确保横坐标按日期分类显示
                tickformat='%m-%d',  # 显示月-日格式
                tickangle=45  # 倾斜标签避免重叠
            ),
            yaxis=dict(
                tickformat='.2f',  # 金额保留两位小数
                tickprefix='¥'  # 添加货币符号
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        chart_json = None
    
    return render_template('statistics.html', chart_json=chart_json)

@app.route('/receivables')
@login_required
def receivables():
    receivables_list = Receivable.query.filter_by(user_id=current_user.id).order_by(Receivable.created_at.desc()).all()
    
    # 计算统计数据
    total_amount = sum(r.amount for r in receivables_list)
    received_amount = sum(r.amount for r in receivables_list if r.status == 'received')
    pending_amount = total_amount - received_amount
    total_count = len(receivables_list)
    
    return render_template('receivables.html', 
                         receivables=receivables_list,
                         total_amount=total_amount,
                         received_amount=received_amount,
                         pending_amount=pending_amount,
                         total_count=total_count)

@app.route('/receivables/add', methods=['GET', 'POST'])
@edit_required
def add_receivable():
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        due_date_str = request.form.get('due_date')
        notes = request.form.get('notes', '')
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        receivable = Receivable(
            title=title,
            amount=amount,
            due_date=due_date,
            notes=notes,
            user_id=current_user.id
        )
        
        db.session.add(receivable)
        db.session.commit()
        flash('应收款添加成功', 'success')
        return redirect(url_for('receivables'))
    
    return render_template('add_receivable.html')

@app.route('/receivables/<int:id>/receive')
@edit_required
def receive_receivable(id):
    receivable = Receivable.query.filter_by(id=id, user_id=current_user.id).first()
    if receivable:
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
    receivable = Receivable.query.filter_by(id=id, user_id=current_user.id).first()
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
    
    # 生产环境配置
    app.run(host='0.0.0.0', port=5085, debug=False) 