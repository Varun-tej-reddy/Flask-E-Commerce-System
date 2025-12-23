import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask import current_app
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, Product, CartItem
from .forms import LoginForm, ProductForm
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from .models import User, Product, CartItem, Orders, OrderItem

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.user_dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html', form=form)


# Registration route using LoginForm for simplicity
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('User already exists.')
        else:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                username=form.username.data,
                password=hashed_password,
                role='user'
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Account created. Please log in.')
            return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))

    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

@main.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    from config import Config
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))

    form = ProductForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(Config.UPLOAD_FOLDER, filename))

        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_filename=filename
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully.')
        return redirect(url_for('main.admin_dashboard'))
    else:
        print("Form errors:", form.errors)

    return render_template('add_product.html', form=form)

@main.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing_item:
        existing_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash('Item added to cart.')
    return redirect(url_for('main.user_dashboard'))

@main.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    grand_total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, grand_total=grand_total)

@main.route('/remove_from_cart/<int:item_id>', methods=['GET', 'POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You are not authorized to remove this item.')
        return redirect(url_for('main.view_cart'))

    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.')
    return redirect(url_for('main.view_cart'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.')
    return redirect(url_for('main.view_cart'))

@main.route('/update_quantity/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized action.')
        return redirect(url_for('main.view_cart'))

    try:
        new_qty = int(request.form.get('quantity'))
        if new_qty < 1:
            db.session.delete(item)
            flash('Item removed because quantity was set to 0.')
        else:
            item.quantity = new_qty
            flash('Quantity updated.')
        db.session.commit()
    except ValueError:
        flash('Invalid quantity.')

    return redirect(url_for('main.view_cart'))


@main.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All items removed from your cart.')
    return redirect(url_for('main.view_cart'))


@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for('main.view_cart'))

    grand_total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        # Create new order
        order = Orders(user_id=current_user.id)
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_name=item.product.name,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)

        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash('Order placed successfully!')
        return redirect(url_for('main.user_dashboard'))

    return render_template('checkout.html', cart_items=cart_items, grand_total=grand_total)

@main.route('/orders')
@login_required
def order_history():
    orders = Orders.query.filter_by(user_id=current_user.id).order_by(Orders.timestamp.desc()).all()
    return render_template('orders.html', orders=orders)

@main.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data

        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            product.image_filename = filename

        db.session.commit()
        flash('Product updated successfully.')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('edit_product.html', form=form, product=product)

@main.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))
    product = Product.query.get_or_404(product_id)
    # Remove product from carts
    CartItem.query.filter_by(product_id=product.id).delete()
    # If your OrderItem model references product_id as a foreign key:
    # OrderItem.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully.')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/orders')
@login_required
def admin_order_history():
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))
    
    orders = Orders.query.order_by(Orders.timestamp.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@main.route('/manage_products')
@login_required
def manage_products():
    if current_user.role != 'admin':
        return redirect(url_for('main.login'))

    products = Product.query.all()
    return render_template('manage_products.html', products=products)

@main.route('/settings')
@login_required
def settings():

    return render_template('settings.html')

@main.route('/change_password', methods=['POST'])
@login_required
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('main.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('main.settings'))
    
    if check_password_hash(current_user.password, confirm_password):
        flash('New password cannot be the same as the old password.', 'danger')
        return redirect(url_for('main.settings'))
    
    # Update password
    current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return redirect(url_for('main.settings'))

@main.route('/user')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return redirect(url_for('main.login'))
    
    products = Product.query.all()
    return render_template('user_dashboard.html', products=products)

@main.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('main.login'))
