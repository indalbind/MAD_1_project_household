from flask import Flask,render_template,redirect,flash
from models import db
import models

app = Flask(__name__)
app.secret_key = 'your_secret_key' # it help no one can change the cokies data without knowing the key.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Curafix.db'
db.init_app(app)


from routes import *








      

















if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        admin = models.User.query.filter_by(username='admin').first()
        if not admin:
            admin = models.User(username='admin',password='admin',fullname='admin',email_id='email_id',address='address',pincode='pincode',is_admin=True)
            db.session.add(admin)
            db.session.commit()

    app.run( host='127.0.0.1' , port=9000, debug=True)
 