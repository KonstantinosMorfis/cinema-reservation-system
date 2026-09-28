#Imports Βιβλιοθήκες Βάσης Δεδομένων

from pymongo import MongoClient
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from flask import Flask, render_template, request,url_for, redirect, session, flash

import requests



#Αρχικοποίηση flask
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key or app.secret_key == "replace-with-a-long-random-secret":
    raise RuntimeError("Set FLASK_SECRET_KEY to a unique random value before starting")

#Συνδεει την εφαρμογη python με τη βαση δεδομενων
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))

#Αρχικοποίηση DB
db = client["DigitalCinema"]


@app.before_request
def require_role_for_private_pages():
    path = request.path
    if path == "/admin" or path.startswith("/admin/"):
        required_type = "admin_user"
    elif path == "/user":
        required_type = "simple_user"
    else:
        return None
    username = session.get("user")
    if not username:
        return redirect(url_for("login_page"))
    account = db.users.find_one({"username": username})
    if not account or account.get("type") != required_type:
        session.pop("user", None)
        return redirect(url_for("login_page"))




#Δημιουργια αρχικης σελιδας(home) και ορισμος μεθοδων που χρησιμοποιει
@app.route("/", methods=['post', 'get'])  
def home():

   #ελεγχος αν υπαρχουν αλλες ταινιες στη βαση δεδομενων
   movie_found = db.movies.find_one({"movie_title": "Shrek"})

   #αν δεν υπαρχουν προσθετει στη βαση τις παρακατω default ταινιες
   if not movie_found:
    #insert_one προσθετει μια εγγραφη στη βαση δεδομενων στη συλλογη movies με τα συγκεκριμενα πεδια
    db.movies.insert_one({'movie_title': "Shrek", 'movie_duration': "90", 'movie_year_of_production': "2001"})
    db.movies.insert_one({'movie_title': "Cars", 'movie_duration': "117", 'movie_year_of_production': "2006"})
    db.movies.insert_one({'movie_title': "Bee Movie", 'movie_duration': "91", 'movie_year_of_production': "2007"})
  
   #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τις ταινιες στην αρχικη σελιδα
   headings = ("Movie Title", "Movie Duration", "Year of Production")
   
   #στη μεταβλητη coll αποθηκευουμε τη συλλογη movies
   coll = db.movies
   
   #αρχικοποιηση λιστας data
   data=[]

   #στη μεταβλητη movies αποθηκευουμε ολες τις εγγραφες της συλλογης movies με τη μεθοδο find 
   movies = coll.find()

   #για καθε ταινια στη συλλογη movies αποθηκευουμε σε μεταβλητες τις τιμες των πεδιων καθε ταινιας
   for movie in movies:
        a="%s" %movie["movie_title"]
        b="%s" %movie["movie_duration"]
        c="%s" %movie["movie_year_of_production"]
        #τοποθετουμε τις μεταβλητες στην array x και την προσθετουμε στη λιστα data η οποια προβαλεται στη σελιδα home.html
        x=[a,b,c]
        data.append(x)
   
   #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ο χρηστης κατευθυνεται στην σελιδα login_page.html
   if request.method == "POST":
      return redirect(url_for("login_page"))
   else:
      #σε οποιαδηποτε αλλη περιπτωση παραμενει στη σελιδα home.html, επισης οι λιστες headings και data στελνονται στην html για να προβληθουν τα δεδομενα
      return render_template('home.html' , headings=headings, data=data )






#Δημιουργια σελιδας(login) και ορισμος μεθοδων που χρησιμοποιει
@app.route("/login", methods=['post', 'get']) 
def login_page():

   #Γινεται αιτημα στην παρακατω διευθυνση για να παρουμε τα δεδομενα των χωρων
   try:
       response = requests.get("https://restcountries.com/v3.1/all?fields=name", timeout=5)
       response.raise_for_status()
       countries = sorted(country["name"]["common"] for country in response.json())
   except (requests.RequestException, KeyError, TypeError, ValueError):
       countries = ["Greece"]

   #ελεγχουμε αν υπαρχει ο αρχικος admin ως εγγραφη στη συλλογη users 
   #στην περιπτωση που δεν υπαρχει τον δημιουργουμε 
   admin_username = os.environ.get("ADMIN_USERNAME")
   admin_password = os.environ.get("ADMIN_PASSWORD")
   if admin_username and admin_password and admin_password != "replace-with-a-unique-password":
        if not db.users.find_one({"username": admin_username}):
            db.users.insert_one({'fullname': admin_username, 'country': '', 'city': '', 'address': '',
                                 'email': '', 'username': admin_username,
                                 'password': generate_password_hash(admin_password), 'type': 'admin_user'})
   
   #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ελεγχουμε απο ποιο κουμπι προηλθε το αιτημα 
   if request.method == "POST":
            
            #τα κουμπια στην html ειναι τυπου form και ελεγχουμε αν το ονομα τους(bt) ισουται με το αντιστοιχο value(Sign Up), ωστε να καταλαβουμε ποιο κουμπι εχει πατηθει
            if request.form["bt"] == "Sign Up":
                #Sign up

                #απο τα textbox μορφης form παιρνουμε τα δεδομενα που εχουν εισαγει οι χρηστες και τα αποθηκευουμε σε μεταβλητες
                fullname = request.form.get('fullname')
                country = request.form.get('country')
                city = request.form.get('city')
                address = request.form.get('address')
                email = request.form.get('email')
                username = request.form.get('username')
                password = request.form.get('password')
                
                #ελεγχουμε στη βαση δεδομενων αν υπαρχει καποιος με το username ή το email που εισηγαγε ο χρηστης στα textbox
                user_found = db.users.find_one({"username": username})
                email_found = db.users.find_one({"email": email})

                #Aν το ονομα απ το textbox υπαρχει ηδη στη βαση δεδομενων τοτε παραμενει στη σελιδα login και ενημερωνεται πως υπαρχει ηδη το username
                if user_found:
                    message = 'This username already exists'
                    #τα ορισματα message και countries, στελνονται στον κωδικα html (login_page.html) ετσι ωστε να εμφανιστουν στον χρηστη
                    return render_template('login_page.html', message=message, countries=countries)
                
                #Aν το email απ το textbox υπαρχει ηδη στη βαση δεδομενων τοτε παραμενει στη σελιδα login και ενημερωνεται πως υπαρχει ηδη το email
                if email_found:
                    message = 'This email already exists'
                    #τα ορισματα message και countries, στελνονται στον κωδικα html (login_page.html) ετσι ωστε να εμφανιστουν στον χρηστη
                    return render_template('login_page.html', message=message, countries=countries)
                else:
                    #σε οποιαδηποτε αλλη περιπτωση, δημιουργειται εγγραφη με τα στοιχεια που εχουν εισαχθει στα textbox και εισαγωνται στην συλλογη requests μεσω της μεθοδου insert one
                    user_input = {'fullname': fullname, 'country': country, 'city': city, 'address': address,'email': email, 'username': username, 'password': generate_password_hash(password), 'type': "simple_user"}
                    db.requests.insert_one(user_input)

                    #ο χρηστης ανακατευθυνεται στην αρχικη σελιδα και εμφανιζεται μηνυμα για την εξελιξη της εγγραφης του
                    flash('Your request is under review by an admin!')
                    return redirect(url_for("home"))
            else:
                #LOG IN
                
                #απο τα textbox μορφης form παιρνουμε τα δεδομενα που εχουν εισαγει οι χρηστες (username, password) και τα αποθηκευουμε σε μεταβλητες
                username_l = request.form.get('username_l')
                password_l = request.form.get('password_l')
                
                #ελεγχουμε αν υπαρχει χρηστης με αυτο το username και στη συνεχεια αν ειναι admin (πεδιο type)
                username_found = db.users.find_one({"username": username_l})
                admin_check = db.users.find_one({"username": username_l, 'type': "admin_user"})
                
                #αν υπαρχει ο χρηστης
                if username_found:
                    #στη μεταβλητη passwordcheck εκχωρειται ο κωδικος του χρηστη με το username που εισηχθει στο textbox
                    passwordcheck = username_found['password']
                    
                    #ελεγχουμε αμα ο κωδικος που εβαλε ο χρηστης στο textbox ειναι ιδιος με τον κωδικο στη βαση δεδομενων(passwordcheck)
                    #δηλαδη γινεται ταυτοποιηση των στοιχειων
                    if password_l and check_password_hash(passwordcheck, password_l):
                        
                        #αμα ειναι admin (type="admin_user"), δημιουργειται session με το username του και ανακατευθυνεται στη σελιδα του admin
                        if admin_check:
                            session["user"] = username_l
                            return redirect(url_for('admin'))
                        else:
                            #αμα ειναι user (type="simple_user"), δημιουργειται session με το username του και ανακατευθυνεται στη σελιδα του user
                            session["user"] = username_l
                            return redirect(url_for('user'))
                    else:
                        #σε περιπτωση που ο κωδικος ειναι λαθος παραμενει στην login_page και ενημερωνεται με αντιστοιχο μηνυμα
                        message = 'Wrong password'
                        return render_template('login_page.html', message1=message, countries=countries)
                else:
                    #αν δεν υπαρχει ο χρηστης παραμενει στην login_page και ενημερωνεται με αντιστοιχο μηνυμα 
                    message = 'Username not found'
                    return render_template('login_page.html', message1=message, countries=countries)
   else:
        #σε οποιαδηποτε αλλη περιπτωση παραμενει στη σελιδα login_page.html
        return render_template('login_page.html', countries=countries)



    


@app.route('/admin',methods=['POST','GET'])
def admin():
    #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τα requests των χρηστων
    headings_requests = ("Fullname", "Country", "City", "Address", "Email", "Username")

    #στη μεταβλητη requests_coll αποθηκευουμε τη συλλογη requests
    requests_coll = db.requests

    #αρχικοποιηση λιστας request_data
    request_data=[]

    #στη μεταβλητη requests αποθηκευουμε ολες τις εγγραφες της συλλογης requests με τη μεθοδο find
    requests = requests_coll.find()

    #για καθε εγγραφη στη συλλογη requests αποθηκευουμε σε μεταβλητες τις τιμες των πεδιων καθε αιτηματος
    for user in requests:
        a="%s" %user["fullname"]
        b="%s" %user["country"]
        c="%s" %user["city"]
        d="%s" %user["address"]
        e="%s" %user["email"]
        f="%s" %user["username"]
        
        #τοποθετουμε τις μεταβλητες στην array x και την προσθετουμε στη λιστα request_data η οποια προβαλεται στη σελιδα admin_page.html
        x=[a,b,c,d,e,f]
        request_data.append(x)

    #εφοσον ο admin βρισκεται σε session
    if "user" in session:
        message1 = ""
        #στη μεταβλητη user εκχωρουμε το ονομα του χρηστη που ειναι συνδεδεμενος
        user = session["user"]

        #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ελεγχουμε απο ποιο κουμπι προηλθε το αιτημα
        if request.method == "POST":

            #αν πατηθει το κουμπι logout τότε ο χρηστης μεταφερεται στην αρχικη σελιδα (home) και δεν ειναι πλεον συνδεδεμενος
            if request.form.get("logout") == "Logout":
                return redirect(url_for('logout'))
            
            #αν πατηθει το κουμπι approve
            if request.form.get("approve") == "Approve":
                #αν δεν υπαρχει καποιο request για να γινει approved, τοτε ξανακατευθυνεται στην σελιδα του admin
                if  db.requests.count_documents({}) == 0:
                    return redirect(url_for('admin'))
                else:
                    #απο το textbox μορφης form παιρνουμε το username
                    username_to_approve = request.form.get('request_username')
                    
                    #ελεγχουμε αν υπαρχει χρηστης με αυτο το username
                    user_to_approve_found = db.requests.find_one({"username": username_to_approve})

                    #αν το username βρεθηκε, το προσθετει στη συλλογη users και το διαγραφει απο τη συλλογη requests
                    if user_to_approve_found:                        
                        db.users.insert_one(user_to_approve_found)
                        db.requests.delete_one({"username": username_to_approve})
                        return redirect(url_for('admin'))
                    else:
                        #αν δεν βρεθει το username τοτε τον ενημερωνει με αντιστοιχο μηνυμα
                        message1 = 'username not found'
            
            #αν πατηθει το κουμπι reject           
            if request.form.get("reject") == "Reject":
                #αν δεν υπαρχει καποιο request για να γινει Reject, τοτε ξανακατευθυνεται στην σελιδα του admin
                if  db.requests.count_documents({}) == 0:
                    return redirect(url_for('admin'))
                else:
                    #απο το textbox μορφης form παιρνουμε το username
                    username_to_reject = request.form.get('request_username')

                    #ελεγχουμε αν υπαρχει χρηστης με αυτο το username
                    user_to_reject_found = db.requests.find_one({"username": username_to_reject})

                    #αν το username βρεθηκε, το προσθετει στη συλλογη users και το διαγραφει απο τη συλλογη requests
                    if user_to_reject_found:
                        db.requests.delete_one({"username": username_to_reject})
                        return redirect(url_for('admin'))
                    else:
                        #αν δεν βρεθει το username τοτε τον ενημερωνει με αντιστοιχο μηνυμα
                        message1 = 'username not found'

            #αν πατηθει το κουμπι user management, τοτε ανακατευθυνεται στην αντιστοιχη σελιδα        
            if request.form.get("user_management") == "User Management":
                return redirect(url_for('user_management'))
            
            #αν πατηθει το κουμπι movie management, τοτε ανακατευθυνεται στην αντιστοιχη σελιδα   
            if request.form.get("movie_management") == "Movie Management":
                return redirect(url_for('movie_management'))
        
        #οσο δεν υπαρχει καποιο post request, ο χρηστης παραμενει στο admin page και περνιουνται τα ορισματα για να εμφανιστουν τα αναλογα δεδομενα
        return render_template('admin_page.html', username=user, message = message1, headings=headings_requests , data=request_data )
    else:

        #εφοσον ο admin δεν βρισκεται σε session, ανακατευθυνεται στην αρχικη σελιδα (home)
        return redirect("/")








@app.route('/admin/user_management',methods=['POST','GET'])
def user_management():

    #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τα στοιχεια ολων των χρηστων της συλλογης users
    headings_users = ("Fullname", "Country", "City", "Address", "Email", "Username", "Type")

    #στη μεταβλητη users_coll αποθηκευουμε τη συλλογη users
    users_coll = db.users

    #αρχικοποιηση λιστας users_data
    users_data=[]
    
    #στη μεταβλητη users αποθηκευουμε ολες τις εγγραφες της συλλογης users με τη μεθοδο find
    users = users_coll.find()

    #για καθε εγγραφη στη συλλογη users αποθηκευουμε σε μεταβλητες τις τιμες των πεδιων καθε user
    for user in users:
        a="%s" %user["fullname"]
        b="%s" %user["country"]
        c="%s" %user["city"]
        d="%s" %user["address"]
        e="%s" %user["email"]
        f="%s" %user["username"]
        g="%s" %user["type"]

        #τοποθετουμε τις μεταβλητες στην array x και την προσθετουμε στη λιστα users_data η οποια προβαλεται στη σελιδα user_management_page.html
        x=[a,b,c,d,e,f,g]
        users_data.append(x)

    #εφοσον ο admin βρισκεται σε session
    if "user" in session:
        message1 = ""
        #στη μεταβλητη user εκχωρουμε το ονομα του χρηστη που ειναι συνδεδεμενος
        user = session["user"]

        #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ελεγχουμε απο ποιο κουμπι προηλθε το αιτημα
        if request.method == "POST":

            #αν πατηθει το κουμπι logout τότε ο χρηστης μεταφερεται στην αρχικη σελιδα (home) και δεν ειναι πλεον συνδεδεμενος
            if request.form.get("logout") == "Logout":
                return redirect(url_for('logout'))
            
            #αν πατηθει το κουμπι Delete
            if request.form.get("delete_user") == "Delete":

                    #απο το textbox μορφης form παιρνουμε το username
                    user_to_delete = request.form.get('username')
                    
                    #ελεγχουμε αν υπαρχει χρηστης με αυτο το username
                    user_to_delete_found = db.users.find_one({"username": user_to_delete})
                    
                    #αν το username βρεθηκε, διαγραφει τον χρηστη απο τη συλλογη (users) οπως και τα reservations που εχει δημιουργησει
                    if user_to_delete_found:
                        db.users.delete_one({"username":user_to_delete})
                        db.reservation.delete_many({"username":user_to_delete})
                        return redirect(url_for('user_management'))
                    else:
                        #αν δεν βρεθει το username τοτε τον ενημερωνει με αντιστοιχο μηνυμα
                        message1 = 'Username not found'

            #αν πατηθει το κουμπι Make admin
            if request.form.get("make_admin") == "Make Admin":
                
                    #απο το textbox μορφης form παιρνουμε το username
                    user_to_change_type = request.form.get('username')

                    #ελεγχουμε αν υπαρχει χρηστης με αυτο το username
                    user_to_change_found = db.users.find_one({"username": user_to_change_type})
                    
                    #αν το username βρεθηκε, ενημερωνει την εγγραφη του χρηστη αυτου
                    if user_to_change_found:
                        db.users.update_one({ "username": user_to_change_type },{ "$set": {"type": "admin_user"}})
                        return redirect(url_for('user_management'))
                    else:
                        #αν το username δεν βρεθηκε τοτε τον ενημερωνει με αντιστοιχο μηνυμα
                        message1 = 'Username not found'

            #αν πατηθει το κουμπι Make user           
            if request.form.get("make_user") == "Make User":

                    #απο το textbox μορφης form παιρνουμε το username
                    user_to_change_type = request.form.get('username')

                    #ελεγχουμε αν υπαρχει χρηστης με αυτο το username
                    user_to_change_found = db.users.find_one({"username": user_to_change_type})

                    #αν το username βρεθηκε, ενημερωνει την εγγραφη του χρηστη αυτου
                    if user_to_change_found:
                        db.users.update_one({ "username": user_to_change_type },{ "$set": {"type": "simple_user"}})
                        return redirect(url_for('user_management'))
                    else:
                        #αν το username δεν βρεθηκε τοτε τον ενημερωνει με αντιστοιχο μηνυμα
                        message1 = 'Username not found'
                        
            #αν πατηθει το κουμπι Back            
            if request.form.get("back") == "Back":
                #επιστρεφει τον χρηστη στη σελιδα admin_page.html
                return redirect(url_for('admin'))


        #οσο δεν υπαρχει καποιο post request, ο χρηστης παραμενει στο user_management_page και περνιουνται τα ορισματα για να εμφανιστουν τα αναλογα δεδομενα       
        return render_template('user_management_page.html' , username=user, message = message1, headings_users = headings_users, users_data = users_data)
        





@app.route('/admin/movie_management',methods=['POST','GET'])
def movie_management():

    #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τα στοιχεια ολων των ταινιων
    headings = ("Movie Title", "Movie Duration", "Year of Production")

    #στη μεταβλητη coll αποθηκευουμε τη συλλογη movies
    coll = db.movies

    #αρχικοποιηση λιστας data
    data=[]
    
    #στη μεταβλητη movies αποθηκευουμε ολες τις εγγραφες της συλλογης movies με τη μεθοδο find
    movies = coll.find()
    
    #για καθε εγγραφη στη συλλογη movies αποθηκευουμε σε μεταβλητες τις τιμες των πεδιων καθε movies
    for movie in movies:
        a="%s" %movie["movie_title"]
        b="%s" %movie["movie_duration"]
        c="%s" %movie["movie_year_of_production"]

        #τοποθετουμε τις μεταβλητες στην array x και την προσθετουμε στη λιστα data η οποια προβαλεται στη σελιδα movie_management_page.html
        x=[a,b,c]
        data.append(x)

    #εφοσον ο admin βρισκεται σε session    
    if "user" in session:
        message1 = ""
        #στη μεταβλητη user εκχωρουμε το ονομα του χρηστη που ειναι συνδεδεμενος
        user = session["user"]

        #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ελεγχουμε απο ποιο κουμπι προηλθε το αιτημα
        if request.method == "POST":

            #αν πατηθει το κουμπί Βack
            if request.form.get("back") == "Back":
                #επιστρεφει τον χρηστη στη σελιδα admin_page.html
                return redirect(url_for('admin'))

            #αν πατηθει το κουμπι logout τότε ο χρηστης μεταφερεται στην αρχικη σελιδα (home) και δεν ειναι πλεον συνδεδεμενος
            if request.form.get("logout") == "Logout":
                return redirect(url_for('logout'))

            #αν πατηθει το κουμπί Add movie 
            if request.form.get("add_movie") == "Add Movie":

                #απο τα textbox μορφης form παιρνουμε τα δεδομενα που εχουν εισαγει o admin (movie_title, movie_duration, movie_year_of_production) και τα αποθηκευουμε σε μεταβλητες
                movie_title = request.form.get('movie_title')
                movie_duration = request.form.get('movie_duration')
                movie_year_of_production = request.form.get('movie_year_of_production')
                
                #δημιουργουμε μια εγγραφη με τα παραπανω δεδομενα και την προσθετουμε στη συλλογη movies
                movie_input = {'movie_title': movie_title, 'movie_duration': movie_duration, 'movie_year_of_production': movie_year_of_production}
                db.movies.insert_one(movie_input)
                return redirect(url_for('movie_management'))
            
            #αν πατηθει το κουμπί Update movie 
            if request.form.get("update_movie") == "Update Movie":

                #απο τα textbox μορφης form παιρνουμε τα δεδομενα που εχουν εισαγει o admin (movie_title, movie_duration, movie_year_of_production) και τα αποθηκευουμε σε μεταβλητες
                movie_title = request.form.get('movie_title_up')
                movie_duration = request.form.get('movie_duration_up')
                movie_year_of_production = request.form.get('movie_year_of_production_up')
                
                #δημιουργουμε μια εγγραφη με τα παραπανω δεδομενα ωστε στην συνέχεια να ενημερωσουμε τις αντιστοιχες τιμες 
                movie_input = {'movie_title': movie_title, 'movie_duration': movie_duration, 'movie_year_of_production': movie_year_of_production}                
                db.movies.update_one({ "movie_title": movie_title },{ "$set": {"movie_title": movie_title}})
                db.movies.update_one({ "movie_title": movie_title },{ "$set": {"movie_duration": movie_duration}})
                db.movies.update_one({ "movie_title": movie_title },{ "$set": {"movie_year_of_production": movie_year_of_production}})
                return redirect(url_for('movie_management'))

            #αν πατηθει το κουμπί Delete movie
            if request.form.get("delete") == "Delete Movie":
                    
                    #απο το textbox μορφης form παιρνουμε τον τιτλο της ταινίας που εχει εισαγει ο admin
                    movie_to_delete = request.form.get('movie_title_to_del')
                    
                    #ελεγχουμε αν υπαρχει ταινια με αυτο τον τιτλο
                    movie_to_delete_found = db.movies.find_one({"movie_title": movie_to_delete})
                    
                    #αν βρεθηκε τοτε τη διαγραφουμε απο τη συλλογη movies
                    if movie_to_delete_found:
                        db.movies.delete_one({"movie_title": movie_to_delete})
                        return redirect(url_for('movie_management'))
                    else:
                        #αν δεν βρεθηκε, εμφανιζουμε το αντιστοιχο μηνυμα
                        message1 = 'Movie not found'
    
    #οσο δεν υπαρχει καποιο post request, ο χρηστης παραμενει στο movie_management_page και περνιουνται τα ορισματα για να εμφανιστουν τα αναλογα δεδομενα
    return render_template('movie_management_page.html' , username=user, message = message1, headings_users = headings, users_data = data)








@app.route('/user',methods=['POST','GET'])
def user():
    #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τα στοιχεια ολων των ταινιών της συλλογης movies
    headings = ("Movie Title", "Movie Duration", "Year of Production")

    #στη μεταβλητη coll αποθηκευουμε τη συλλογη movies
    coll = db.movies

    #αρχικοποιηση λιστας data
    data=[]

    #στη μεταβλητη movies αποθηκευουμε ολες τις εγγραφες της συλλογης movies με τη μεθοδο find
    movies = coll.find()

    #για καθε εγγραφη στη συλλογη movies αποθηκευουμε σε μεταβλητες τις τιμες των πεδιων καθε movies
    for movie in movies:
        a="%s" %movie["movie_title"]
        b="%s" %movie["movie_duration"]
        c="%s" %movie["movie_year_of_production"]
        
        #τοποθετουμε τις μεταβλητες στην array x και την προσθετουμε στη λιστα data η οποια προβαλεται στη σελιδα user_page.html
        x=[a,b,c]
        data.append(x)


    #αρχικοποιηση headings που χρησιμοποιουνται για την προβολη του πινακα με τα στοιχεια των κρατησεων
    headings1 = ("Movie Title", "Ticket Number")

    #στη μεταβλητη coll1 αποθηκευουμε τη συλλογη reservation
    coll1 = db.reservation
    
    #αρχικοποιηση λιστας booking_data
    booking_data=[]

    #στη μεταβλητη reservations αποθηκευουμε ολες τις εγγραφες της συλλογης reservation με τη μεθοδο find
    reservations = coll1.find()


    #στη μεταβλητη user εκχωρουμε το ονομα του χρηστη που ειναι συνδεδεμενος 
    user = session["user"]

    #για καθε εγγραφη στη συλλογη reservation
    for book in reservations:
        
        #εκχωρουμε στις μεταβλητες(k,i) μονο τις κρατησεις του χρηστη ο οποιος ειναι συνδεδεμενος
        if book["username"] == user:
            k="%s" %book["movie_title"]
            i="%s" %book["ticket_number"]

            #τοποθετουμε τις μεταβλητες στην array y και την προσθετουμε στη λιστα booking_data η οποια προβαλεται στη σελιδα user_page.html
            y=[k,i]
            booking_data.append(y)



    if "user" in session:
        message1 = ""
        #στη μεταβλητη user εκχωρουμε το ονομα του χρηστη που ειναι συνδεδεμενος
        user = session["user"]
        
        #αν ληφθει μυνημα Post (δηλαδη πατηθει καποιο κουμπι) ελεγχουμε απο ποιο κουμπι προηλθε το αιτημα
        if request.method == "POST":

            #αν πατηθει το κουμπι logout τότε ο χρηστης μεταφερεται στην αρχικη σελιδα (home) και δεν ειναι πλεον συνδεδεμενος
            if request.form.get("logout") == "Logout":
                return redirect(url_for('logout'))
                
            #αν πατηθει το κουμπι Book Ticket    
            if request.form.get("book_ticket") == "Book Ticket":
                
                #απο το textbox μορφης form παιρνουμε τον τιτλο της ταινίας που θα γίνει κράτηση και ποσα εισητηρια θέλει να κλείσει ο user
                movie_to_book = request.form.get('movie_title_to_book')
                ticket_number = request.form.get('ticket_number')

                #ελεγχουμε αν υπαρχει ταινια με αυτο τον τιτλο
                movie_to_book_found = db.movies.find_one({"movie_title": movie_to_book})
                
                #αν βρεθηκε τοτε προσθετουμε τα παραπανω δεδομενα στη συλλογη reservation
                if movie_to_book_found:
                    db.reservation.insert_one({'movie_title': movie_to_book, 'username': user, 'ticket_number': ticket_number})
                    return redirect(url_for('user'))
                else:
                    
                    #αν δεν βρεθηκε, εμφανιζουμε το αντιστοιχο μηνυμα
                    message1 = 'Movie not found'
                    
        #ο χρηστης παραμενει στο user_page και περνιουνται τα ορισματα για να εμφανιστουν τα αναλογα δεδομενα        
        return render_template('user_page.html', username=user, message = message1 , headings_users = headings, users_data = data, headings_users1 = headings1, users_data1 = booking_data)
    else:

        #εφοσον ο user δεν βρισκεται σε session, ανακατευθυνεται στην αρχικη σελιδα (home)
        return redirect("/")





@app.route('/logout')
def logout():
    #το session του χρήστη τελειώνει και ο χρήστης ανακατευθείνεται στην αρχική σελίδα
    session.pop("user", None)
    return redirect("/")

#ανοιγεί τον server στο localhost
if __name__ == "__main__":
    app.run()


    
