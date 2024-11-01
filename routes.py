from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, session
from models import db, User, Service, ServiceRequest, Professional, Review
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from app import app


# --------------------------- decoretor ------------------------
# every time cheaking is seesion it not good and also some wher loop whole also are there
# @auth_required decorator is preventing users who are not logged in from accessing the thing 
def auth_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session and 'professional_id' not in session:
            flash("Please log in to continue.")
            return redirect(url_for('login'))
        return func(*args,**kwargs)
    return inner


def admin_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('You nead to login first')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])    
        if not user.is_admin:
            flash("you are not authorized to view this page")
            return redirect(url_for('index'))
        return func(*args,**kwargs)    
    return inner
    
# ---------------------------------------------------------------









#  ----------- 🏎️🏎️😎😎😎😎😎😎👉😎🙏🧡🧡🧡⚠️⚠️⚠️⚠️ ----------------------------------
# ----------------------------------- home page ----------------------------------------------------------
@app.route('/')
@auth_required
def index():
    if 'professional_id' in session:  # If the professional
        professional = Professional.query.get(session['professional_id'])
        if not professional:
            flash(' please log in again')
            return redirect(url_for('login'))
        return redirect(url_for('professional'))


    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found, please log in again')
            return redirect(url_for('login'))
        
        if user.is_admin:
            return redirect(url_for('admin'))
        
        show_service = request.args.get('service')
        if show_service:
            user_service_request = Service.query.filter(
                Service.name.ilike(f"%{show_service}%")).all()
        else:
            user_service_request = []

        service_request =  ServiceRequest.query.filter(ServiceRequest.customer_id == user.id).all()    


        return render_template('index.html', user=user,Service = Service.query.all(),user_service_request = user_service_request,service_request = service_request,show_service = show_service) # this is the user page 🧡🧡🧡🧡 so the index.html for user 

    flash('You are not logged in. Please log in first.')
    return redirect(url_for('login'))


# ---------- login (user and admin) ---------
@app.route('/login')
def login():
    return render_template('login.html')

# --------- ordering the service
@app.route('/order/<int:service_id>', methods=['GET'])
@auth_required  # Ensure only logged-in users can order
def ordering(service_id):
    if 'user_id' not in session:
        flash('Please login to continue')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])    
    service = Service.query.get(service_id)
    if not service:
        flash('Sorry we are working on it')
        return redirect(url_for('index'))

    requested_service = ServiceRequest(
        service_id=service.id,
        customer_id=user.id,
        professional_id=None,  # You can assign it later
        
    )
    db.session.add(requested_service)
    db.session.commit()
    flash('sucess fully orderd ')
    return redirect(url_for('index'))



# closing the service and submeting the review

@app.route('/review', methods=['GET', 'POST'])
@auth_required
def review():
    if request.method == "POST":
        service_request_id = request.form.get('service_request_id')
        rating = request.form.get('rating')
        comment = request.form.get('comment')


        service_request = ServiceRequest.query.get(service_request_id)

        user = User.query.get(session['user_id'])
        review = Review(
            service_request_id=service_request.id,
            customer_id=user.id,
            professional_id=service_request.professional_id,
            rating=rating,
            comment=comment
        )

        db.session.add(review)
        service_request.status = "completed"
        service_request.date_of_completion = datetime.utcnow().date()
        db.session.commit()

        flash("Request closed and review submitted.")
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    service_request_id = request.args.get('id')
    service_request = ServiceRequest.query.get(service_request_id)

    return render_template('review.html', request = service_request, user = user)



# Login route (POST) automatic run when any one click on login button because every thing in post in login.html
# Modify login_post to handle admin login
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Username or password cannot be empty")
        return redirect(url_for('login'))

    # First, try to find the user in the User table
    user = User.query.filter_by(username=username).first()
    if user:
        if user.check_password(password):  # Password check
            # Set the session for a user or admin
            session['user_id'] = user.id
            session.pop('professional_id', None)  # Ensure professional session is cleared if logging in as user
            if user.is_admin:
                flash(f"Welcome  {user.username}!",'success')
                return redirect(url_for('admin'))
            else:
                flash(f"Welcome {user.username}!","success")
                return redirect(url_for('index'))
        else:
            flash("Incorrect password")
            return redirect(url_for('login'))




    # If no user is found, try finding the professional
    professional = Professional.query.filter_by(username=username).first()

    if professional:
        if professional.check_password(password):  # Password check
            # Clear any existing user session to avoid conflict
            session.pop('user_id', None)

            # Set the session for a professional
            session['professional_id'] = professional.id
            flash(f"Welcome {professional.username}!","success")
            return redirect(url_for('index'))
        else:
            flash("Incorrect password")
            return redirect(url_for('login'))

    # If neither a user nor a professional is found
    flash("Invalid login credentials")
    return redirect(url_for('login'))


# ------------------------------------------------------------------------------------------------------
#  ----------- 🏎️🏎️😎😎😎😎😎😎👉😎🙏🧡🧡🧡 ----------------------------------















# ---------- logout -------------

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('professional_id', None)
    flash("You have been logged out")
    return redirect(url_for('login'))



# ---------------------------  register ----------------------------------------------

# -----------------user register -------------------
# Register routes (get)
@app.route('/register')
def register():
    return render_template('register.html')


# register routes (post)
@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    pincode = request.form.get('pincode')

    if not username or not password:
        flash("Username or password cannot be empty")
        return redirect(url_for('register'))

    if User.query.filter_by(username=username).first():
        flash("This username is already taken")
        return redirect(url_for('register'))

    # Create a new user and commit to the database
    user = User(username=username, password=password, fullname=fullname, email_id=email_id, address=address, pincode=pincode)
    db.session.add(user)
    db.session.commit()
    flash(f"{user.username} register sucessfully")
    return redirect(url_for('login'))
# ----------------------------------------------------------




# -------------------------------------------------------------------------------------



# ------------  profile updatation ------------------

# -----------------  profile so that use can view edit the details --------------
# profile get
@app.route('/profile')
@auth_required
def profile():
    # if 'user_id' not in session: 👈 this indexing thing koo we put in decorator
    #     flash("Please log in to continue.")
    #     return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html',user = user)

@app.route('/profile', methods = ["POST"])
@auth_required
def profile_post():
    user = User.query.get(session['user_id'])

    username = request.form.get('username')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    fullname = request.form.get('fullname')
    email_id = request.form.get('email_id')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    if not username or not password or not cpassword:
        flash("Usernmae and password can not be empty")
        return redirect(url_for('profile'))
    if not user.check_password(cpassword):
        flash("Incorrect password")
        return redirect(url_for('profile'))
    
    if User.query.filter_by(username=username).first() and username != user.username:      
        flash("please select some other user name because this user already exist")
        return redirect(url_for('profile'))
    
    user.username = username
    user.password = password
    user.fullname = fullname
    user.email_id = email_id
    user.address = address
    user.pincode = pincode

    db.session.commit()
    flash('Profile sucessfully updated')
    return redirect(url_for('profile'))
# -----------------------------------------------------

# --------------------------------------------------------------------------------------------------------------




# ------------------------------------------------ admin -------------------------------------------------
@app.route('/admin')
@admin_required
def admin():
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash("You are not allow to view this page")
        return redirect(url_for('index'))
    return render_template('admin.html',userall = User.query.all(),user = user,service = Service.query.all(),professional = Professional.query.all(),service_request = ServiceRequest.query.all())    


# --------------------(service) for add the service -------------------
@app.route('/service/add')
@admin_required
def add_services():
    return render_template('service/add.html',user=User.query.get(session['user_id']))

@app.route('/service/add', methods = ['POST'])
@admin_required
def add_services_post():
    name = request.form.get('name')
    description = request.form.get('description')
    base_price = request.form.get('baseprice')
    # basic validation
    if name == "":
        flash("service name can not be empty")
        return redirect(url_for('add_services'))
    if len(name)>100:
        flash("service name can not be greater than 100")    
        return redirect(url_for('add_services'))

    service = Service(name=name,description=description,base_price=base_price)
    db.session.add(service)
    db.session.commit()
    flash('service added sucessfully')
    return redirect(url_for('admin'))
# -----------------------------------------------------------------



# ---------------------- show the perticular service -----------------------
@app.route('/service/<int:id>/show')
@admin_required
def show_service(id):
    return render_template('service/show.html',user = User.query.get(session['user_id']), service = Service.query.get(id))


# dummy route in show product 
@app.route('/service/<int:service_id>/add-product')
@admin_required
def add_product(service_id):
    return render_template('product/add.html',user = User.query.get(session['user_id']), service = Service.query.get(service_id))

@app.route('/service/<int:service_id>/add-product',methods = ['POST'])
@admin_required
def add_product_post(service_id):
    pass

# editing the showing product where we able to do edit and delete 
@app.route('/product/<int:id>/edit')
@admin_required
def edit_product(id):
    return render_template('product/edit.html',user = User.query.get(session['user_id']), service = Service.query.get(id)) # 👈👈👈👈

@app.route('/product/<int:id>/edit', methods = ['POST'])
@admin_required
def edit_product_post(id):
    pass

# delete that showing product 
@app.route('/product/<int:id>/delete')
@admin_required
def delete_product(id):
    services = Service.query.get(id)
    if not services:
        flash('service not exist')
        redirect(url_for('admin'))
    return render_template('product/delete.html',user = User.query.get(session['user_id']), service = services) # 👈👈👈👈

@app.route('/product/<int:id>/delete', methods = ['POST'])
@admin_required
def delete_product_post(id):
    services = Service.query.get(id)
    if not services:
        flash('service not exist')
        redirect(url_for('admin'))
    db.session.delete(services)    
    db.session.commit()
    flash("service deleted sucss fully")
    return redirect(url_for('admin'))




# ------------------------------------------------------------


#-----------------------  edit the perticular service -------------------
@app.route('/service/<int:id>/edit')
@admin_required
def edit_service(id):
    return render_template('service/edit.html',user=User.query.get(session['user_id']),service = Service.query.get(id))

@app.route('/service/<int:id>/edit', methods = ['POST'])
@admin_required
def edit_service_post(id):
    name = request.form.get('name')
    description = request.form.get('description')
    base_price = request.form.get('baseprice')
    if name == "":
        flash("Service can not be empty")
        return redirect(url_for('edit_service', id = id))
    if len(name) > 100:
        flash('Service name can not be greater than 100')    
        return redirect(url_for('edit_service', id = id))
    

    service = Service.query.get(id)
    service.name = name
    service.description = description
    service.base_price = base_price
    db.session.commit()
    flash('service update sucessfully')
    return redirect(url_for('admin'))

# ------------------------------------------------------------



# --------------------------  delete perticular service  😯😯😯😯😯😯😯 -----------------

@app.route('/service/<int:id>/delete')
@admin_required
def delete_service(id):
    return render_template('service/delete.html',user = User.query.get(session['user_id']), service = Service.query.get(id)) 

@app.route('/service/<int:id>/delete', methods = ['POST'])
@admin_required
def delete_service_post(id):
    service = Service.query.get(id)
    if not service:
        flash('Category does not exist')
        return redirect(url_for('admin'))
    db.session.delete(service)    
    db.session.commit()
    flash('Category deleted sucessfully')
    return redirect(url_for('admin'))

# --------------------------------------------------------------




# -----------------all professional thing ---------------------- 

# showing all detail of professional
@app.route('/professional/<int:id>/show') # end must be using overall other wise crate problem
@admin_required
def show_professional(id):
    return render_template('service/show_prof.html',professional = Professional.query.get(id),is_admin=True)





# approve the professional 
@app.route('/professional/<int:id>/approve')
@admin_required
def approve_professional(id):
    professional = Professional.query.get(id)
    professional.approved = True
    db.session.commit() 
    flash(f"you approve {professional.username} ")
    return redirect(url_for('admin'))



# blocking the professional
@app.route('/professional/<int:id>/block')
@admin_required
def reject_professional(id):
    professional = Professional.query.get(id)
    professional.blocked = True
    db.session.commit()
    flash(f"you block {professional.username} ")
    return redirect(url_for('admin'))


# unblocking
@app.route('/professional/<int:id>/unblock')
@admin_required
def unblock_professional(id):
    professional = Professional.query.get(id)
    professional.blocked = False
    db.session.commit()
    flash(f"you block {professional.username} ")
    return redirect(url_for('admin'))


# delete the professional 😯😯😯😯😯😯😯
@app.route('/professional/<int:id>/delete')
@admin_required
def delete_professional(id):
    professional = Professional.query.get(id)
    if not professional:
        flash("this professional not exist")
        return redirect(url_for('admin'))
    
    db.session.delete(professional)    
    db.session.commit()
    flash(f"you deleted professional {professional.fullname}")
    return redirect(url_for('admin'))



# user block,unblock,delete

@app.route('/user/<int:id>/block')
@admin_required
def reject_user(id):
    user = User.query.get(id)
    user.blocked = True
    db.session.commit()
    flash(f"you block {user.username} ")
    return redirect(url_for('admin'))


# delete part
@app.route('/user/<int:id>/delete')
@admin_required
def delete_user(id):
    user = User.query.get(id)
    if not user:
        flash("this professional not exist")
        return redirect(url_for('admin'))
    
    db.session.delete(user)    
    db.session.commit()
    flash(f"you deleted professional {user.fullname}")
    return redirect(url_for('admin'))

# unblock user
@app.route('/user/<int:id>/unblock')
@admin_required
def unblock_user(id):
    user = User.query.get(id)
    user.blocked = False
    db.session.commit()
    flash(f"you unblock {user.username} ")
    return redirect(url_for('admin'))



# ------------ admin search or user serch   -----------

@app.route('/search')
@auth_required
def search():
    user = User.query.get(session['user_id'])
    parameter = request.args.get('parameter')
    query = request.args.get('query')
    
    results = []
    headers = []

    if user.is_admin:
        if parameter == 'service_request' and query != 'False':
            service_requests = ServiceRequest.query.filter(ServiceRequest.status.ilike('%'+ query +'%')).all()
            headers = ['Request ID', 'Service Name', 'Customer Name', 'Professional Name', 'Date of Request', 'Date of Completion', 'Status', 'Remarks']
            for sr in service_requests:
                results.append(
                    {
                        'Request ID': sr.id,
                        'Service Name': sr.service.name,
                        'Customer Name': sr.requesting_customer.fullname,
                        'Professional Name': sr.assigned_professional.fullname,
                        'Date of Request': sr.date_of_request,
                        'Date of Completion': sr.date_of_completion,
                        'Status': sr.status,
                        'Remarks': sr.remarks
                    } 
                )

        elif parameter == 'user' and query:
            users = User.query.filter(User.fullname.ilike('%'+ query +'%')).all()
            headers = ['User ID', 'Username', 'Full Name', 'Email', 'Address', 'Pincode', 'Block_Status']
            for u in users:
                results.append(
                    {
                        'User ID': u.id,
                        'Username': u.username,
                        'Full Name': u.fullname,
                        'Email': u.email_id,
                        'Address': u.address,
                        'Pincode': u.pincode,
                        'Block_Status': u.blocked
                    } 
                )
        elif parameter == 'professional' and query:
            professionals = Professional.query.filter(Professional.fullname.ilike('%'+ query +'%')).all()
            headers = ['Professional ID', 'Username', 'Full Name', 'Service Name', 'Experience', 'Address', 'Pincode']
            for p in professionals:
                results.append(
                    {
                        'Professional ID': p.id,
                        'Username': p.username,
                        'Full Name': p.fullname,
                        'Service Name': p.service_name,
                        'Experience': p.experience,
                        'Address': p.address,
                        'Pincode': p.pincode,
                        'Approved': p.approved,
                        'Blocked': p.blocked
                    } 
                )
        elif parameter == 'service' and query:
            services = Service.query.filter(Service.name.ilike('%'+ query +'%')).all()
            headers = ['Service ID', 'Name', 'Description', 'Base Price']
            for s in services:
                results.append(
                    {
                        'Service ID': s.id,
                        'Name': s.name,
                        'Description': s.description,
                        'Base Price': s.base_price
                    } 
                )
        elif parameter == 'review' and query:
            reviews = Review.query.filter(Review.comment.ilike('%'+ query +'%')).all()
            headers = ['Review ID', 'Service Request ID', 'Customer ID', 'Professional ID', 'Rating', 'Comment']
            for r in reviews:
                results.append(
                    {
                        'Review ID': r.id,
                        'Service Request ID': r.service_request_id,
                        'Customer ID': r.customer_id,
                        'Professional ID': r.professional_id,
                        'Rating': r.rating,
                        'Comment': r.comment
                    } 
                ) 

        return render_template('admin_search.html', user=user, results=results, headers=headers, parameter=parameter)
    else:
        if parameter == 'name' and query:
            fetchall = Service.query.filter(Service.name.ilike(f'%{query}%')).all()
            headers = ['ID', 'Description', 'ServiceName', 'Price']
            for data in fetchall:
                results.append(
                    {
                    'ID': data.id,
                    'Description': data.description,
                    'ServiceName': data.name,
                    'Price': str(data.base_price)+' ₹'
                    }
                )

        elif parameter == 'price' and query:
            fetchall = Service.query.filter(Service.base_price.ilike(f'%{query}%')).all()
            headers = ['ID', 'Description', 'ServiceName', 'Price']
            for data in fetchall:
                results.append(
                    {
                    'ID': data.id,
                    'Description': data.description,
                    'ServiceName': data.name,
                    'Price': str(data.base_price)+' ₹'
                    }
                )
        return render_template('user_search.html', user=user,  results=results, headers=headers, parameter=parameter)

 










# ------------------------------------------------------------------------




# ----------- user or admin summary 😯😯😯 this is in pending for the pie chart of review) ---------
@app.route('/summary')
@auth_required
def summary():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        requests = ServiceRequest.query.all()

        # Extract service IDs and the number of requests
        service_ids = list(set([req.service_id for req in requests]))  # Unique IDs
        request_counts = [ServiceRequest.query.filter_by(service_id=service_id).count() for service_id in service_ids]

        # Pass data to the template
        return render_template('admin_summary.html', user=user, service_ids=service_ids, request_counts=request_counts)
    else:
        requested = ServiceRequest.query.filter_by(customer_id=user.id).count()
        closed = ServiceRequest.query.filter_by(customer_id=user.id, status='completed').count()
        assigned = ServiceRequest.query.filter_by(customer_id=user.id).filter(ServiceRequest.status == 'True').count()
        status = ['Requested', 'Closed', 'Assigned']
        counts = [requested, closed, assigned]

        return render_template('user_summary.html',user = user, status= status,counts=counts)

# -----------------------------




# ---------------------------------------------------------------------------------------------------------------------




# -------------------------------------------------😋 professional register ------------------------------------------

# --------------------- professional register --------------------

UPLOAD_FOLDER = 'static/professional_resume'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/professional_register')
def professional_register():
    services = Service.query.all()
    return render_template('professional_register.html',services = services)



@app.route('/professional_register', methods=['POST'])
def professional_registser_post():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname')
    service_name = request.form.get('service_name')
    experience = request.form.get('experience')
    pdf_file = request.files['pdf_file']  
    address = request.form.get('address')
    pincode = request.form.get('pincode')

    # Check for username and password
    if not username or not password:
        flash("Username or password cannot be empty")
        return redirect(url_for('professional_register'))

    # Check if the username already exists
    if Professional.query.filter_by(username=username).first():
        flash("This username is already taken")
        return redirect(url_for('professional_register'))

    # Check if a PDF file was uploaded and if it's valid
    if pdf_file:
        filename = secure_filename(pdf_file.filename)  # Secure the filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(file_path)  # Save the file in the upload folder
    else:
        flash("Please upload a valid PDF file.")
        return redirect(url_for('professional_register'))
    
    professional = Professional( username=username,password=password,fullname=fullname,service_name=service_name,experience=experience,pdf_file=file_path,address=address,pincode=pincode)

    db.session.add(professional)
    db.session.commit()
    flash(f"{professional.username} registered successfully")
    return redirect(url_for('login'))




# -------------------------------------------------------------------------------




# ---------------------------------🤔🤔 professional dashboard,summary,search,profile ------------------------

from profes import *



# ------------------------------------------------------------------------------------------------------------------------



