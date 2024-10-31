from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, session
from models import db, User, Service, ServiceRequest, Professional, Review
from werkzeug.utils import secure_filename
from app import app
import os

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

    
# ---------------------------------------------------------------





#  ----------------- professional dashboard -------------------------------------------------------------
@app.route('/professional')
@auth_required
def professional():
    professional = Professional.query.get(session['professional_id'])  # Get logged-in professional

    if professional.approved and not professional.blocked:
        professional_service_name = professional.service_name
        service = Service.query.filter_by(name=professional_service_name).first()

        if not service:
            flash("Service type not found.")
            return redirect(url_for('professional_dashboard'))

        # Fetch all service requests related to this professional's service
        service_requests = ServiceRequest.query.filter_by(service_id=service.id).all()

        # Filter out service requests rejected by this professional and those already accepted by others
        pending_requests = [
            req for req in service_requests
            if not req.has_rejected(professional.id) and req.status == "False"
        ]

        # Fetch only accepted requests by this professional
        my_services = ServiceRequest.query.filter_by(professional_id=professional.id, status="True").all()

        # Fetch closed/completed services for this professional
        closed_services = ServiceRequest.query.filter_by(professional_id=professional.id, status="completed").all()

        return render_template('professional_dashboard.html',
                               professional=professional,
                               service_requests=pending_requests,
                               my_services=my_services,
                               closed_services=closed_services)

    elif professional.blocked:
        return render_template('block.html')

    return render_template('404.html')
# ---------------------------------------------------------




# ------------ handling the service request which given by user ------------

@app.route('/professional/<int:id>/accept')
@auth_required
def accept_service(id):
    professional_id = session['professional_id']  # Get the logged-in professional's ID
    request = ServiceRequest.query.get(id)
    
    if request.status == "True":  # Check if the service has already been accepted
        flash(f"Service {request.service.name} has already been accepted by another professional.")
        return redirect(url_for('professional'))
    
    request.status = "True"
    request.professional_id = professional_id  # Assign this request to the logged-in professional
    
    db.session.commit()  # Save changes to the database
    
    flash(f"You accepted {request.service.name} successfully.")
    return redirect(url_for('professional'))




# reject mean's cancelled the service mena's i not do 
@app.route('/professional/<int:id>/reject')
@auth_required
def reject_service(id):
    professional_id = session['professional_id']
    request = ServiceRequest.query.get(id)

    # Add the professional's ID to the rejected list
    request.add_rejecting_professional(professional_id)

    db.session.commit()  # Save the changes in the database

    flash("You have rejected this service request.")
    return redirect(url_for('professional'))




# drop service if prfessioanl by mistake click on accepted
@app.route('/professional/<int:id>/drop')
@auth_required
def drop_service(id):
    request = ServiceRequest.query.get(id)
    request.status= "False"
    request.professional_id = None
    db.session.commit() 
    flash(f"you drop {request.service.name} ")
    return redirect(url_for('professional'))

# ----------------------------------------------------------------








# -------------------------------------------- profile part  -----------------------------
UPLOAD_FOLDER = 'static/professional_resume'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/professional/profile', methods=['GET', 'POST'])
def professional_profile():
    professional = Professional.query.get(session['professional_id'])

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        fullname = request.form.get('fullname')
        pdf_file = request.files.get('pdf_file')  # Handle file uploads
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        # Check for empty fields
        if not username or not cpassword:
            flash("Username and current password cannot be empty")
            return redirect(url_for('professional_profile'))

        # Check if the current password is correct
        if not professional.check_password(cpassword):
            flash("Incorrect current password")
            return redirect(url_for('professional_profile'))

        # Check for unique username
        existing_user = Professional.query.filter_by(username=username).first()
        if existing_user and existing_user.id != professional.id:
            flash("This username is already taken. Please choose another.")
            return redirect(url_for('professional_profile'))

        # Update fields
        professional.username = username
        if password:  # Update password only if a new password is provided
            professional.password = password
            

        professional.fullname = fullname

        # Handle the file upload
        if pdf_file and pdf_file.filename.endswith('.pdf'):  # Validate it's a PDF
            pdf_filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            pdf_file.save(pdf_path)
            professional.pdf_file = pdf_path  # Update the pdf_file path in the database
        elif pdf_file:
            flash("Please upload a valid PDF file.")
            return redirect(url_for('professional_profile'))

        if address:
            professional.address = address
        if pincode:
            professional.pincode = pincode
        db.session.commit()
        flash('Profile successfully updated')
        return redirect(url_for('professional_profile'))

    return render_template('professional_profile.html', professional=professional)


# -------------------------------------------------------------------------------------           

# ------------------------ professional search part -----------------
@app.route('/professional/search')
def professional_search():
    professional = Professional.query.get(session['professional_id'])
    parameter = request.args.get('parameter')
    query = request.args.get('query')
    results = []
    headers = []
    if query:
        if parameter == 'username':
            users = User.query.filter(User.username.ilike('%' + query + '%')).all()
        elif parameter == 'pincode':
            users = User.query.filter(User.pincode.ilike('%' + query + '%')).all()
        elif parameter == 'address':
            users = User.query.filter(User.address.ilike('%' + query + '%')).all()
        elif parameter == 'date_of_request':
            users = User.query.join(ServiceRequest).filter(ServiceRequest.date_of_request.ilike('%' + query + '%')).all()
        else:
            users = User.query.filter(User.fullname.ilike('%' + query + '%')).all()

        headers = ['User ID', 'Username', 'Full Name', 'Email', 'Address', 'Pincode', 'Status','Date']
        for user in users:
            if user.requests_made:
                latest_request = user.requests_made[-1] 
                status = latest_request.status
                date = latest_request.date_of_request
            else:
                status = 'No Requests'
            results.append({
                'User ID': user.id,
                'Username': user.username,
                'Full Name': user.fullname,
                'Email': user.email_id,
                'Address': user.address,
                'Pincode': user.pincode,
                'Status': status, 
                'Date' : date
            })
        
        return render_template('professional_search.html', professional=professional, results=results, headers=headers)

    return render_template('professional_search.html', professional=professional)
# ----------------------------------                      ---------------





# ----------------------------------------- summary ---------------------------------- 
@app.route('/professional/summary')
def professional_summary():
    professional1 = Professional.query.get(session['professional_id'])
    professional_id = session.get('professional_id')
    professional_service_name = professional1.service_name
    service = Service.query.filter_by(name=professional_service_name).first()
    total_requests = ServiceRequest.query.filter_by(service_id = service.id).count()

    received_requests = ServiceRequest.query.filter_by(professional_id = professional_id).count()
    closed_requests = ServiceRequest.query.filter_by(professional_id = professional_id, status='completed').count()
    rejected_requests = ServiceRequest.query.filter( ServiceRequest.rejected_by_professional_id.like(f"%{professional_id}%"),
                                                     ServiceRequest.professional_id == professional_id).count()

    return render_template('professional_summary.html', 
                           received_requests=received_requests, 
                           closed_requests=closed_requests, 
                           rejected_requests=rejected_requests,professional=professional,total_requests = total_requests)


# ----------------------------------------------------------------------------------------