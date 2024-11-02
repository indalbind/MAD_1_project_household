from flask_sqlalchemy import SQLAlchemy
from datetime import date 
# securely handling password, where i use generate_password_hash for incription in password so that 
# password store in data base incripted and cheak_password_has is use for chaking the enterd password
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email_id = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    blocked = db.Column(db.Boolean,nullable = False,default = False)

    # Relationships
    # backref because automatically the back realtion make let i make realtion between A to B 
    # using backref the relation automatically make between B to A
    requests_made = db.relationship('ServiceRequest', backref='requesting_customer', lazy=True,cascade="all, delete-orphan")  # Unique backref
    reviews_written = db.relationship('Review', foreign_keys='Review.customer_id', backref='customer', lazy=True)  # Changed backref to 'customer'

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)  # Consistent with User
    fullname = db.Column(db.String(150), nullable=False)
    service_name = db.Column(db.String(150), nullable=False)
    experience = db.Column(db.String(100), nullable=False)
    pdf_file = db.Column(db.String(200), nullable=False)  # Store path to uploaded file
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean,nullable = False,default = False)
    # Relationships
    requests_handled = db.relationship('ServiceRequest', backref='assigned_professional', lazy=True,cascade="all, delete-orphan")  # Unique backref
    reviews_received = db.relationship('Review', foreign_keys='Review.professional_id', backref='professional', lazy=True,cascade="all, delete-orphan")  # 😋😋Unique backref
    
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    base_price = db.Column(db.Float, nullable=False)

    # Relationships
    requests = db.relationship('ServiceRequest', backref='service', lazy=True,cascade="all, delete-orphan")


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=True)
    date_of_request = db.Column(db.Date, nullable=False, default=date.today) 
    date_of_completion = db.Column(db.Date) 
    status = db.Column(db.String(30), nullable=False,default = "False")  # e.g., 'Pending', 'Completed', 'Cancelled'
    remarks = db.Column(db.String(200))
    rejected_by_professional_id = db.Column(db.String(255), nullable=True) # Update to store a comma-separated list of rejecting professionals

    # Relationships
    reviews = db.relationship('Review', backref='service_request', lazy=True,cascade="all, delete-orphan")

    
    def add_rejecting_professional(self, professional_id):
        # Add professional ID to rejection list if not already present
        if self.rejected_by_professional_id:
            rejected_ids = self.rejected_by_professional_id.split(',')
            if str(professional_id) not in rejected_ids:
                rejected_ids.append(str(professional_id))
            self.rejected_by_professional_id = ','.join(rejected_ids)
        else:
            self.rejected_by_professional_id = str(professional_id)

    def has_rejected(self, professional_id):
        # Check if professional has rejected this service request
        if self.rejected_by_professional_id:
            return str(professional_id) in self.rejected_by_professional_id.split(',')
        return False





class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # e.g., 1-5 stars
    comment = db.Column(db.String(255))


