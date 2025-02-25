import re
from datetime import datetime, timedelta
from importlib.metadata import requires
# from multiprocessing.managers import view_type

import pymongo
# from Scripts.unicodedata import category
from bson import ObjectId
from dns.e164 import query
from flask import Flask, render_template, request, session
from numpy.ma.core import append
from pyexpat.errors import messages
from werkzeug.utils import redirect
import os

from Mail import send_email

APPLICATION_PATH=os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH=APPLICATION_PATH+"./static/Book_Profiles"
app=Flask(__name__)
app.secret_key='library_management'
my_client=pymongo.MongoClient("mongodb://localhost:27017")
my_database=my_client["library_management"]
admin_collection=my_database["admin"]
location_collection=my_database["locations"]
member_collection=my_database["member"]
librarian_collection=my_database["librarian"]
category_collection=my_database["category"]
book_collection=my_database["book"]
borrowings_collection=my_database["borrowings"]
payments_collection=my_database["payments"]
reserve_collection=my_database["reserve"]


query = {}
count = admin_collection.count_documents(query)
if count == 0:
    query = {"username": "admin", "password": "admin"}
    admin_collection.insert_one(query)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin_login")
def admin_login():
    message=request.args.get("message")
    if message == None:
        message = ""
    return render_template("admin_login.html", message=message)

@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username=request.form.get("username")
    password=request.form.get("password")
    query={"username":username, "password":password}
    count=admin_collection.count_documents(query)
    if count>0:
        admin=admin_collection.find_one(query)
        session['admin_id']=str(admin['_id'])
        session['role'] = "admin"
        return redirect("/admin_home")
    else:
        return redirect("/admin_login?message=invalid login details")

@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/logout")
def logout():
    session.clear()
    return  render_template("index.html")

@app.route("/categories")
def categories():
    message = request.args.get("message")
    if message == None:
        message = ""
    query = {}
    categories = category_collection.find(query)
    categories = list(categories)
    return render_template("categories.html", categories=categories, message=message)

@app.route("/categories_action", methods=['post'])
def categories_action():
    category_name = request.form.get("category_name")
    query = {"category_name":category_name}
    count=category_collection.count_documents(query)
    if count > 0:
        return redirect("/categories?message=Duplicate Category Details")
    query = {"category_name": category_name}
    category_collection.insert_one(query)
    return redirect("/categories?message=Category Added Successfully")

@app.route("/member_registration")
def member_registration():
    return  render_template("member_registration.html")

@app.route("/member_registration_action" , methods=['post'])
def member_registration_action():
     first_name=request.form.get("first_name")
     last_name=request.form.get("last_name")
     email= request.form.get("email")
     phone= request.form.get("phone")
     password= request.form.get("password")
     age= request.form.get("age")
     gender=request.form.get("gender")
     address=request.form.get("address")
     if member_collection.count_documents({"email":email})>0:
         return render_template("message.html",message="this mail is already exists")
     new_member={"first_name":first_name,"last_name":last_name,"email":email,"phone":phone,"password":password,"age":age,"gender":gender,"address":address}
     member_collection.insert_one(new_member)
     return render_template("message.html", message="Data Inserted Successfully")

@app.route("/member_login")
def member_login():
    return  render_template("member_login.html")

@app.route("/member_login_action", methods=['post'])
def member_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = member_collection.count_documents(query)
    if count > 0:
        member =member_collection.find_one(query)
        session['member_id'] = str(member['_id'])
        session['role'] = 'member'
        return redirect("/member_home")
    else:
        return render_template("message.html", message="invalid login details")

@app.route("/member_home")
def member_home():
   return render_template("member_home.html")

@app.route("/librarian_registration")
def Librarian_registration():
    locations=location_collection.find()
    locations = list(locations)
    query = {}
    librarians = librarian_collection.find(query)
    librarians = list(librarians)
    return render_template("librarian_registration.html",locations=locations, librarians=librarians)

@app.route("/librarian_registration_action",methods=['post'])
def librarian_registration_action():
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        password = request.form.get("password")
        gender=request.form.get("gender")
        location_id=request.form.get("location_id")
        status = "UnAuthorized"
        query = {"email": email}
        count = librarian_collection.count_documents(query)
        if count > 0:
            return render_template("message.html", message="duplicate email address")
        query = {"phone": phone}
        count = librarian_collection.count_documents(query)
        if count > 0:
            return render_template("message.html", message="Duplicate Phone")
        query = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone, "address": address,"password": password, "gender":gender, "status":status, "location_id":ObjectId(location_id)}
        librarian_collection.insert_one(query)
        return render_template("message.html", message="librarian Registration Successfully")

@app.route("/active_library")
def active_library():
    librarian_id=request.args.get("librarian_id")
    query1={"_id":ObjectId(librarian_id)}
    query2={"$set":{"status":"Authorized"}}
    librarian_collection.update_one(query1, query2)
    return redirect("/librarian_registration")

@app.route("/deactive_library")
def deactive_library():
    librarian_id=request.args.get("librarian_id")
    query1={"_id":ObjectId(librarian_id)}
    query2={"$set":{"status":"UnAuthorized"}}
    librarian_collection.update_one(query1, query2)
    return redirect("/librarian_registration")

@app.route("/librarian_login")
def librarian_login():
    return render_template("librarian_login.html")

@app.route("/librarian_login_action", methods=['post'])
def librarian_login_action():
    email = request.form.get("email")
    password = request.form.get("password")

    query = {"email": email, "password": password}
    count = librarian_collection.count_documents(query)
    if count > 0:
        librarian = librarian_collection.find_one(query)
        if librarian['status']=='Authorized':
            session['librarian_id'] = str(librarian['_id'])
            session['role'] = 'librarian'
            return redirect("/librarian_home")
        else:
            return render_template("message.html", message="Your Account Not Authorized")
    else:
        return render_template("message.html", message="invalid login details")


@app.route("/librarian_home")
def librarian_home():
     return render_template("librarian_home.html")

@app.route("/add_locations")
def add_locations():
    message = request.args.get("message")
    if message == None:
        message = ""
    query = {}
    locations = location_collection.find(query)
    locations = list(locations)
    return render_template("add_location.html", locations=locations, message=message)

@app.route("/add_location_action", methods=['post'])
def add_location_action():
    location_name = request.form.get("location_name")
    query = {"location_name":location_name}
    count=location_collection.count_documents(query)
    if count > 0:
        return redirect("/add_locations?message=Duplicate Location Details")
    query = {"location_name": location_name}
    location_collection.insert_one(query)
    return redirect("/add_locations?message=Location Added Successfully")

@app.route("/books")
def books():
    message = request.args.get("message")
    if message == None:
        message = ""
    keyword = request.args.get("keyword")
    if keyword == None:
        keyword = ''
    query = {}
    if session['role']=='librarian':
        if keyword!="":
            librarian_id= session['librarian_id']
            keyword2 = re.compile(".*" + str(keyword) + ".*", re.IGNORECASE)

            query = {"$or": [{"book_name": keyword2}, {"author": keyword2},
                             {"description": keyword2}],"book_copies.librarian_id":ObjectId(librarian_id)}

        else:
            librarian_id = session['librarian_id']
            query = {"book_copies.librarian_id": ObjectId(librarian_id),}
    else:
        keyword2 = re.compile(".*" + str(keyword) + ".*", re.IGNORECASE)
        query = {"category_name": keyword2}
        categories = category_collection.find(query)
        categories = list(categories)
        category_ids = []
        for category in categories:
            category_ids.append(category['_id'])
        query = {"$or": [{"category_id": {"$in": category_ids}}, {"book_name": keyword2}, {"author": keyword2},
                         {"description": keyword2}]}
    books = book_collection.find(query)
    books = list(books)
    categories=category_collection.find()
    categories = list(categories)
    if session['role']=='librarian':
        librarian = librarian_collection.find_one({'_id':ObjectId(session['librarian_id'])})
        locations = location_collection.find({'_id':ObjectId(librarian['location_id'])})
        locations = list(locations)
        print(locations)
    else:
        locations = location_collection.find()
        locations = list(locations)
        print(locations)
    return render_template("books.html", books=books, locations=locations,categories=categories, message=message,get_category_by_category_id=get_category_by_category_id,get_location_by_location_id=get_location_by_location_id)

@app.route("/add_book_action", methods=['post'])
def add_book_action():
    book_name = request.form.get("book_name")
    category_id = request.form.get("category_id")
    location_id = request.form.get("location_id")
    picture = request.files.get("picture")
    path = PROFILE_PATH + "/" + picture.filename
    picture.save(path)
    author = request.form.get("author")
    price = request.form.get("price")
    available_copies = request.form.get("available_copies")
    description = request.form.get("description")
    book_copies = []
    if session['role'] == 'librarian':
        librarian_id = session['librarian_id']
        query = {"_id": ObjectId(librarian_id)}
        librarian = librarian_collection.find_one(query)
        location_id = librarian['location_id']
        for i in range(1, int(available_copies) + 1):
            book_copy = {"location_id": location_id, "book_copy_number": i, "librarian_id": ObjectId(librarian_id)}
            book_copies.append(book_copy)
    new_book = {"book_name": book_name, "category_id": ObjectId(category_id), "picture": picture.filename,"author": author, "price": price, "available_copies": available_copies, "description": description,"book_copies": book_copies,"location_id":location_id}
    book_collection.insert_one(new_book)
    return redirect("/books?message=Book Added Successfully")

def get_location_by_location_id(location_id):
    query={"_id":location_id}
    location=location_collection.find_one(query)
    return location

def get_category_by_category_id(category_id):
    query={"_id":category_id}
    category=category_collection.find_one(query)
    return category


def get_category_by_category_id(category_id):
    query={"_id":category_id}
    category=category_collection.find_one(query)
    return category

@app.route("/view_book")
def view_book():
    keyword=request.args.get("keyword")
    query = {}
    if keyword==None:
        keyword=''
    if keyword!="":
        keyword2=re.compile(".*"+str(keyword)+".*",re.IGNORECASE)
        query = {"$or": [{"book_name": keyword2}, {"author": keyword2},
                         {"description": keyword2}]}
    else:
        query = {}
    books=book_collection.find(query)
    books=list(books)
    return render_template("/view_book.html", books=books,keyword=keyword,get_category_by_category_id=get_category_by_category_id, is_book_borrowed_by_member=is_book_borrowed_by_member,get_location_by_location_id=get_location_by_location_id)

@app.route("/add_book_copies")
def add_book_copies():
    query={}
    book_id=request.args.get("book_id")
    locations=location_collection.find(query)
    locations=list(locations)
    return render_template("add_book_copies.html",book_id=book_id, locations=locations)

@app.route("/add_book_copies_action")
def add_book_copies_action():
    book_id=request.args.get("book_id")
    location_id=request.args.get("location_id")
    number_of_copies=request.args.get("number_of_copies")
    librarian_id= session["librarian_id"]
    query={"_id":ObjectId(book_id)}
    book=book_collection.find_one(query)
    print(book)
    if 'book_copies' in book:
        book_copies = book['book_copies']
        last_book_copy_number = len(book['book_copies'])
    else:
        book_copies = []
        last_book_copy_number = 1
    for i in range(last_book_copy_number,int(number_of_copies)+last_book_copy_number):
        book_copy={"location_id":ObjectId(location_id), "book_copy_number":i+1, "librarian_id":ObjectId(librarian_id)}
        book_copies.append(book_copy)

    query1={"_id":ObjectId(book_id)}
    query2={"$set":{"book_copies":book_copies}}
    book_collection.update_one(query1,query2)
    return redirect("view_book?message=Book Copies Added Successfully")

@app.route("/book_copies")
def book_copies():
    book_id=request.args.get("book_id")
    print(book_id)
    query = {"_id": ObjectId(book_id)}
    book = book_collection.find_one(query)
    print(book)
    location_books = {}
    for book_copy in book['book_copies']:
        if str(book_copy['location_id'])+str(book_id)+str(book_copy['librarian_id']) in location_books:
            location_books[str(book_copy['location_id'])+str(book_id)+str(book_copy['librarian_id'])]['number_of_copies'] = location_books[str(book_copy['location_id'])+str(book_id)+str(book_copy['librarian_id'])]['number_of_copies'] + 1
        else:
            location_books[str(book_copy['location_id'])+str(book_id)+str(book_copy['librarian_id'])] =  {"location_id": book_copy['location_id'], "librarian_id": book_copy['librarian_id'], "number_of_copies":1}
    return render_template("book_copies.html",location_books=location_books, get_location_by_location_id=get_location_by_location_id, get_librarian_by_librarian_id=get_librarian_by_librarian_id, book_id=book_id, get_available_books_by_librarian_id=get_available_books_by_librarian_id, is_notification_reserved=is_notification_reserved)

@app.route("/send_request")
def send_request():
    book_id=request.args.get("book_id")
    print(book_id)
    location_id=request.args.get("location_id")
    librarian_id=request.args.get("librarian_id")
    member_id=session['member_id']
    date=datetime.now()
    query = {"book_id": ObjectId(book_id), "location_id":ObjectId(location_id), "librarian_id":ObjectId(librarian_id), "member_id":ObjectId(member_id), "date":date, "status":"book requested"}
    borrowings_collection.insert_one(query)
    return render_template("mmsg.html",message="Request sent successfully")

@app.route("/cancel_request")
def cancel_request():
    borrowing_id = request.args.get("borrowing_id")
    print(borrowing_id)
    query1={"_id":ObjectId(borrowing_id)}
    query2={"$set":{"status":"book request cancelled"}}
    borrowings_collection.update_one(query1,query2)
    return redirect("borrowings?message=book request cancelled")

@app.route("/assign_book")
def assign_book():
    borrowing_id = request.args.get("borrowing_id")
    query= {"_id": ObjectId(borrowing_id)}
    borrowing = borrowings_collection.find_one(query)
    book = book_collection.find_one({"_id":borrowing['book_id']})
    book_copies = []
    for book_copy in book['book_copies']:
        if str(book_copy['librarian_id']) == str(borrowing['librarian_id']) and str(book_copy['location_id']) == str(borrowing['location_id']):
            book_copies.append(book_copy)
    print(book_copies)
    return render_template("assign_book.html", borrowing=borrowing, book_copies=book_copies, get_librarian_by_librarian_id=get_librarian_by_librarian_id, get_location_by_location_id=get_location_by_location_id, is_book_assigned=is_book_assigned )

@app.route("/assign_book_action")
def assign_book_action():
    borrowing_id=request.args.get("borrowing_id")
    book_copy_number=request.args.get("book_copy_number")
    borrowed_date = datetime.now()
    return_date = borrowed_date + timedelta(days=15)
    query1={"_id":ObjectId(borrowing_id)}
    query2={"$set":{"status":"book borrowed","book_copy_number":book_copy_number, "borrowed_date": borrowed_date, "return_date": return_date}}
    borrowings_collection.update_one(query1,query2)
    return redirect("/borrowings?view_type=borrowings&message=Book Assigned")

@app.route("/return_book")
def return_book():
    borrowing_id=request.args.get("borrowing_id")
    librarian_id = request.args.get("librarian_id")
    fine = request.args.get("fine")
    query = {"_id": ObjectId(librarian_id)}
    librarian = librarian_collection.find_one(query)
    location_id = librarian['location_id']
    query={"_id":ObjectId(borrowing_id)}
    borrowing = borrowings_collection.find_one(query)
    book_id = borrowing['book_id']

    query1={"_id":ObjectId(borrowing_id)}
    if fine==None:
        query2={"$set":{"status":"book return request", "return_location_id":location_id, "return_librarian_id": ObjectId(librarian_id), "status2": "Location Change Requested"}}
    else:
        query2={"$set":{"status":"book return request", "return_location_id":location_id, "return_librarian_id": ObjectId(librarian_id), "fine": fine, "status2": "Location Change Requested"}}
    borrowings_collection.update_one(query1,query2)
    return redirect("/borrowings?message=Book Return Request")

def get_librarians():
    librarians = librarian_collection.find({})
    librarians = list(librarians)
    return librarians

@app.route("/renewal_book")
def renewal_book():
    borrowing_id = request.args.get("borrowing_id")
    query = {"_id": ObjectId(borrowing_id)}
    borrowing=borrowings_collection.find_one(query)
    return_date=borrowing['return_date']
    return_date=return_date+timedelta(days=15)
    query2={"$set":{"status":"book renewed", "return_date":return_date}}
    borrowings_collection.update_one(query,query2)
    return redirect("/borrowings?message=Book renewed")




@app.route("/edit_location")
def edit_location():
    location_id = request.args.get("location_id")
    query = {"_id": ObjectId(location_id)}
    location = location_collection.find_one(query)
    return render_template("edit_location.html",location=location,location_id=location_id)



@app.route("/edit_locations_action")
def edit_locations_action():
    location_id = request.args.get("location_id")
    location_name = request.args.get("location_name")
    query = {"$set": {"location_name": location_name}}
    location_collection.update_one({"_id": ObjectId(location_id)}, query)
    return redirect("/add_locations")



@app.route("/edit_genre")
def edit_genre():
    category_id = request.args.get("category_id")
    query = {"_id": ObjectId(category_id)}
    category = category_collection.find_one(query)
    return render_template("edit_genre.html",category=category,category_id=category_id)


@app.route("/edit_category_action")
def edit_category_action():
    category_id = request.args.get("category_id")
    category_name = request.args.get("category_name")
    query = {"$set": {"category_name": category_name}}
    category_collection.update_one({"_id": ObjectId(category_id)}, query)
    return redirect("/categories")


@app.route("/collect_book")
def collect_book():
    borrowing_id = request.args.get("borrowing_id")
    query1={"_id":ObjectId(borrowing_id)}
    query2={"$set":{"status":"book returned"}}
    borrowings_collection.update_one(query1,query2)
    borrowing = borrowings_collection.find_one(query1)
    query = {"book_id": borrowing['book_id'], "librarian_id": borrowing['librarian_id'], "status": "Notification Requested"}
    reserves = reserve_collection.find(query)
    for reserve in reserves:
        query = {"_id": reserve['_id']}
        query2 = {"$set": {"book_id": borrowing['book_id'], "librarian_id": borrowing['librarian_id'], "status": "Notified"}}
        reserve_collection.update_one(query, query2)
        print("Notified")
        book = book_collection.find_one({"_id":ObjectId(borrowing['book_id'])})
        member_id = reserve['member_id']
        member = member_collection.find_one({"_id":ObjectId(member_id)})
        send_email("Book Available","Hi "+str(member['first_name'])+" "+str(member['last_name'])+" , The "+str(book['book_name'])+" is available now",member['email'])

        # *************************************************
    return redirect("borrowings?view_type=history&message=Book Collected")

@app.route("/borrowings")
def borrowings():
    message = request.args.get("message")
    if message == None:
        message = ""
    if session['role']=='member':
        member_id=session['member_id']
        query={"member_id":ObjectId(member_id)}
    elif session['role'] == 'librarian':
        librarian_id=session['librarian_id']
        view_type=request.args.get("view_type")
        if view_type=='requests':
            query={"librarian_id":ObjectId(librarian_id), "status":"book requested"}
        elif view_type=='borrowings':
            query={"$or":[{"librarian_id":ObjectId(librarian_id),"status":"book borrowed"}, {"librarian_id":ObjectId(librarian_id),"status":"book renewed"}, {"return_librarian_id":ObjectId(librarian_id),"status":"book return request", "status2":"Location Change Request Accepted"}, {"librarian_id":ObjectId(librarian_id),"status":"book return request", "status2":"Location Change Request Rejected"}]}
        elif view_type=='history':
            query={"$or":[{"librarian_id":ObjectId(librarian_id),"status":"book returned"}, {"return_librarian_id":ObjectId(librarian_id),"status":"book returned"}, {"librarian_id":ObjectId(librarian_id),"status":"book request cancelled"}]}
    else:
        query = {"status2": "Location Change Requested"}
    print(query)
    borrowings=borrowings_collection.find(query)
    borrowings=list(borrowings)
    borrowings.reverse()
    return render_template("borrowings.html",borrowings=borrowings, get_book_by_book_id=get_book_by_book_id, get_librarian_by_librarian_id=get_librarian_by_librarian_id, get_location_by_location_id=get_location_by_location_id, get_member_by_member_id=get_member_by_member_id, get_librarians=get_librarians, str=str, get_fine_by_borrowing_id=get_fine_by_borrowing_id, message=message, check_is_same_location=check_is_same_location)

@app.route("/borrowings2")
def borrowings2():
    message = request.args.get("message")
    if message == None:
        message = ""
    member_id=session['member_id']
    query={"$or":[{"member_id":ObjectId(member_id),"status":"book borrowed"}, {"member_id":ObjectId(member_id),"status":"book renewed"}]}
    borrowings=borrowings_collection.find(query)
    borrowings=list(borrowings)
    borrowings.reverse()
    return render_template("borrowings2.html",borrowings=borrowings, get_book_by_book_id=get_book_by_book_id, get_librarian_by_librarian_id=get_librarian_by_librarian_id, get_location_by_location_id=get_location_by_location_id, get_member_by_member_id=get_member_by_member_id, get_librarians=get_librarians, str=str, get_fine_by_borrowing_id=get_fine_by_borrowing_id, message=message, check_is_same_location=check_is_same_location, len=len)



def get_location_by_location_id(location_id):
    query = {"_id": ObjectId(location_id)}
    location = location_collection.find_one(query)
    return location

def get_librarian_by_librarian_id(librarian_id):
    query = {"_id": librarian_id}
    print(query)
    librarian = librarian_collection.find_one(query)
    return librarian

def get_book_by_book_id(book_id):
    query = {"_id": ObjectId(book_id)}
    book = book_collection.find_one(query)
    return book

def get_member_by_member_id(member_id):
    query = {"_id": ObjectId(member_id)}
    member = member_collection.find_one(query)
    return member

def get_librarian_by_librarian_name(librarian_name):
    query = {"_id": ObjectId(librarian_name)}
    librarian = librarian_collection.find_one(query)
    return librarian

def get_fine_by_borrowing_id(borrowing_id):
    print("jhiiii")
    query = {"_id": ObjectId(borrowing_id)}
    borrowing = borrowings_collection.find_one(query)
    today = datetime.now()
    if 'return_date' in borrowing:
        return_date = borrowing['return_date']
        if today > return_date:
            diff = today-return_date
            days = diff.days
            print(days)
            return days
        else:
            return 0
    else:
        return 0

@app.route("/pay_fine")
def pay_fine():
    fine = request.args.get("fine")
    borrowing_id = request.args.get("borrowing_id")
    librarian_id = request.args.get("librarian_id")
    return render_template("pay_fine.html", fine=fine, borrowing_id=borrowing_id, librarian_id=librarian_id)

@app.route("/pay_fine_action")
def pay_fine_action():
    fine = request.args.get("fine")
    borrowing_id = request.args.get("borrowing_id")
    librarian_id = request.args.get("librarian_id")
    card_type=request.args.get("card_type")
    card_number=request.args.get("card_number")
    name_on_card=request.args.get("name_on_card")
    cvv=request.args.get("cvv")
    expiry_date=request.args.get("expiry_date")
    query={"librarian_id":ObjectId(librarian_id),"fine":fine,"name_on_card":name_on_card, "card_type":card_type, "card_number":card_number, "cvv": cvv, "expiry_date":expiry_date, "borrowing_id":ObjectId(borrowing_id)}
    payments_collection.insert_one(query)
    return redirect("/return_book?borrowing_id="+str(borrowing_id)+"&librarian_id="+str(librarian_id)+"&fine="+fine)

def is_book_borrowed_by_member(book_id):
    member_id = session['member_id']
    query = {"$or": [{"book_id": ObjectId(book_id), "member_id": ObjectId(member_id), "status": "book requested"},
                     {"book_id": ObjectId(book_id), "member_id": ObjectId(member_id), "status": "book borrowed"},
                     {"book_id": ObjectId(book_id), "member_id": ObjectId(member_id), "status": "book renewed"},
                     {"book_id": ObjectId(book_id), "member_id": ObjectId(member_id), "status": "book return request"}]}
    count = borrowings_collection.count_documents(query)
    if count > 0:
        return True
    else:
        return False

def is_book_assigned(borrowing_id, book_copy_number):
    query = {"_id": borrowing_id}
    borrowing = borrowings_collection.find_one(query)
    print(borrowing)
    book_id = borrowing['book_id']
    query = {"$or": [{"book_id": book_id, "book_copy_number": str(book_copy_number), "status": "book requested"},
                     {"book_id": book_id, "book_copy_number": str(book_copy_number), "status": "book borrowed"},
                     {"book_id": book_id, "book_copy_number": str(book_copy_number), "status": "book renewed"},
                     {"book_id": book_id, "book_copy_number": str(book_copy_number), "status": "book return request"}]}
    print(query)
    count = borrowings_collection.count_documents(query)
    print(count)
    if count > 0:
        return True
    else:
        return False

@app.route("/view_payment")
def view_payment():
    borrowing_id=request.args.get("borrowing_id")
    query={"borrowing_id":ObjectId(borrowing_id)}
    payment=payments_collection.find_one(query)
    return render_template("view_payment.html", payment=payment)

def get_available_books_by_librarian_id(book_id,librarian_id):
    query = {"_id": ObjectId(book_id)}
    book = book_collection.find_one(query)
    available_count = 0
    for book_copy in book['book_copies']:
        if str(book_copy['librarian_id']) == str(librarian_id):
            query = {
                "$or": [{"book_id": ObjectId(book_id), "book_copy_number": str(book_copy['book_copy_number']), "status": "book requested"},
                        {"book_id": ObjectId(book_id), "book_copy_number": str(book_copy['book_copy_number']), "status": "book borrowed"},
                        {"book_id": ObjectId(book_id), "book_copy_number": str(book_copy['book_copy_number']), "status": "book renewed"},
                        {"book_id": ObjectId(book_id), "book_copy_number": str(book_copy['book_copy_number']), "status": "book return request"}]}
            count = borrowings_collection.count_documents(query)
            if count == 0 :
                available_count = available_count + 1
    return available_count

@app.route("/notify_me")
def notify_me():
    book_id = request.args.get("book_id")
    librarian_id = request.args.get("librarian_id")
    member_id = session['member_id']
    query = {"book_id": ObjectId(book_id), "librarian_id": ObjectId(librarian_id), "member_id": ObjectId(member_id), "date": datetime.now(), "status":"Notification Requested"}
    reserve_collection.insert_one(query)

    return render_template("mmsg.html", message = "You will receive Notification, When book is Available")

def is_notification_reserved(book_id,librarian_id):
    query = {"book_id": ObjectId(book_id), "librarian_id": librarian_id, "status": "Notification Requested"}
    print(query)
    count = reserve_collection.count_documents(query)
    if count > 0:
        return True
    else:
        return False

@app.route("/notification")
def notification():
    member_id=session['member_id']
    query={"member_id":ObjectId(member_id)}
    reserves=reserve_collection.find_one(query)
    print(reserves)
    return render_template("notification.html", reserves=reserves, get_book_by_book_id=get_book_by_book_id,get_librarian_by_librarian_id=get_librarian_by_librarian_id,get_member_by_member_id=get_member_by_member_id)
@app.route("/accept_location_change")
def accept_location_change():
    borrowing_id = request.args.get("borrowing_id")
    query = {"_id": ObjectId(borrowing_id)}
    query2 = {"$set": {"status2": "Location Change Request Accepted"}}
    borrowings_collection.update_one(query, query2)
    query = {"_id": ObjectId(borrowing_id)}
    borrowing = borrowings_collection.find_one(query)
    book_id = borrowing['book_id']
    query1 = {"_id":book_id, "book_copies": {"$elemMatch": {"book_copy_number":int(borrowing['book_copy_number'])}}}
    query2 = {"$set": {"book_copies.$.location_id": borrowing["return_location_id"], "book_copies.$.librarian_id": borrowing["librarian_id"] }}
    book_collection.update_one(query1, query2)
    return redirect("/borrowings?message=Return Location Change Request Accepted")

@app.route("/reject_location_change")
def reject_location_change():
    borrowing_id = request.args.get("borrowing_id")
    query = {"_id": ObjectId(borrowing_id)}
    query2 = {"$set": {"status2": "Location Change Request Rejected"}}
    borrowings_collection.update_one(query, query2)
    return redirect("/borrowings?message=Return Location Change Request Rejected")
def check_is_same_location(borrowing_id):
    print("************************************")
    query = {"_id": borrowing_id}
    borrowing = borrowings_collection.find_one(query)
    if str(borrowing['location_id']) == str(borrowing['return_location_id']):
        return True
    if borrowing['status2'] == 'Location Change Request Accepted':
        return True
    if session['role'] == "librarian":
        librarian_id = session['librarian_id']
        librarian = librarian_collection.find_one({"_id":ObjectId(librarian_id)})
        print("hi")
        print(librarian['location_id'])
        print(borrowing['location_id'])
        if str(librarian['location_id']) == str(borrowing['location_id']):
            return True
    return False

@app.route("/return_book2")
def return_book2():
    fine = request.args.get("fine")
    librarian_id = request.args.get("librarian_id")
    member_id = session['member_id']
    if int(fine) == 0:
        query = {"member_id": ObjectId(member_id), "status": "book borrowed", "return_date": {"$gte": datetime.now()} }
        borrowings = borrowings_collection.find(query)
        borrowings = list(borrowings)
        print(borrowings)
        for borrowing in borrowings:
            query = {"_id": ObjectId(librarian_id)}
            librarian = librarian_collection.find_one(query)
            location_id = librarian['location_id']
            query = {"_id": borrowing['_id']}
            borrowing = borrowings_collection.find_one(query)
            query1 = {"_id": borrowing['_id']}
            if fine == 0:
                query2 = {"$set": {"status": "book return request", "return_location_id": location_id,
                                   "return_librarian_id": ObjectId(librarian_id),
                                   "status2": "Location Change Requested"}}
            else:
                query2 = {"$set": {"status": "book return request", "return_location_id": location_id,
                                   "return_librarian_id": ObjectId(librarian_id), "fine": fine,
                                   "status2": "Location Change Requested"}}
            print(query1)
            print(query2)
            borrowings_collection.update_one(query1, query2)
        return render_template("message.html", message="Book Return Requested")
    else:
        librarian_id = request.args.get("librarian_id")
        return render_template("pay_fine2.html", fine=fine, librarian_id=librarian_id)

@app.route("/pay_fine_action2")
def pay_fine_action2():
    member_id = session['member_id']
    fine = request.args.get("fine")
    borrowing_id = request.args.get("borrowing_id")
    librarian_id = request.args.get("librarian_id")
    card_type = request.args.get("card_type")
    card_number = request.args.get("card_number")
    name_on_card = request.args.get("name_on_card")
    cvv = request.args.get("cvv")
    expiry_date = request.args.get("expiry_date")
    query = {"librarian_id": ObjectId(librarian_id), "fine": fine, "name_on_card": name_on_card, "card_type": card_type,
             "card_number": card_number, "cvv": cvv, "expiry_date": expiry_date, "borrowing_id": ObjectId(borrowing_id)}
    payments_collection.insert_one(query)

    query = {"member_id": ObjectId(member_id), "status": "book borrowed", "return_date": {"$lte": datetime.now()}}
    borrowings = borrowings_collection.find(query)
    borrowings = list(borrowings)
    for borrowing in borrowings:
        query = {"_id": ObjectId(librarian_id)}
        librarian = librarian_collection.find_one(query)
        location_id = librarian['location_id']
        query = {"_id": borrowing['_id']}
        borrowing = borrowings_collection.find_one(query)
        query1 = {"_id": borrowing['_id']}
        if fine == 0:
            query2 = {"$set": {"status": "book return request", "return_location_id": location_id,
                               "return_librarian_id": ObjectId(librarian_id),
                               "status2": "Location Change Requested"}}
        else:
            query2 = {"$set": {"status": "book return request", "return_location_id": location_id,
                               "return_librarian_id": ObjectId(librarian_id), "fine": fine,
                               "status2": "Location Change Requested"}}
        print(query1)
        print(query2)
        borrowings_collection.update_one(query1, query2)
    return render_template("message.html", message="Book Return Requested")


app.run(debug=True)

