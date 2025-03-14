from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Task, Post
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Khởi tạo database
db.init_app(app)

# Khởi tạo LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Tạo admin mặc định và database
def init_db():
    with app.app_context():
        # Xóa database cũ và tạo mới
        db.drop_all()
        db.create_all()
        
        # Kiểm tra và tạo admin nếu chưa tồn tại
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True,
                created_at=datetime.utcnow()  # Thêm thời gian tạo
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin account created!')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
            
        # Đăng nhập user
        login_user(user, remember=remember)
        
        # Chuyển hướng dựa vào role
        if user.is_admin:
            return redirect(url_for('user_dashboard'))
        return redirect(url_for('user_dashboard'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Kiểm tra validation
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('Email already registered')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
            
        # Tạo user mới
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    # Lấy tất cả users (trừ admin)
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/dashboard.html', users=users)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Lấy tasks và posts của user
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    user_posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('user/dashboard.html', tasks=user_tasks, posts=user_posts)

# CRUD cho Tasks
@app.route('/tasks')
@login_required
def tasks():
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('user/tasks.html', tasks=user_tasks)

@app.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!')
        return redirect(url_for('tasks'))
    return render_template('user/create_task.html')

@app.route('/tasks/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('tasks'))
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        task.completed = 'completed' in request.form
        db.session.commit()
        flash('Task updated successfully!')
        return redirect(url_for('tasks'))
    return render_template('user/edit_task.html', task=task)

@app.route('/tasks/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('tasks'))
    
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('tasks'))

# CRUD cho Posts
@app.route('/posts')
@login_required
def posts():
    user_posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('user/posts.html', posts=user_posts)

@app.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        link = request.form.get('link')
        
        # Xử lý upload ảnh
        image = request.files.get('image')
        image_url = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'uploads/{filename}'
        
        post = Post(
            title=title,
            content=content,
            link=link,
            image_url=image_url,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!')
        return redirect(url_for('posts'))
    return render_template('user/create_post.html')

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if post.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('posts'))
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.link = request.form.get('link')
        
        # Xử lý upload ảnh mới
        image = request.files.get('image')
        if image and allowed_file(image.filename):
            # Xóa ảnh cũ nếu có
            if post.image_url:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image_url)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post.image_url = f'uploads/{filename}'
        
        db.session.commit()
        flash('Post updated successfully!')
        return redirect(url_for('posts'))
    return render_template('user/edit_post.html', post=post)

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('posts'))
    
    # Xóa ảnh nếu có
    if post.image_url:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image_url)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!')
    return redirect(url_for('posts'))

# Hàm hỗ trợ kiểm tra file ảnh
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Unauthorized access!')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin user!')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Xóa user và tất cả tasks, posts liên quan
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user!')
        print(e)
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 