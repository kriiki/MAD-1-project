

Trekking Management App

This is my project for the course - a web app to manage treks, trek staff and trekkers (users). Made using Flask, SQLite and Bootstrap as required in the problem statement.

What it does

There are 3 types of users:

Admin - already exists in the database, no need to register. can create/edit/delete treks, approve staff, assign staff to treks, see all users/staff/treks, blacklist people, search stuff
Trek Staff - has to register first, then wait for admin to approve before they can use their dashboard. once approved they can see their assigned treks, change slots/status, see who booked
User/Trekker - registers and can login right away (no approval needed). can browse open treks, filter by difficulty/location, book a trek, see their bookings
How to run it
First make a virtual env (so it doesnt mess with your other python stuff):
python -m venv venv
Activate it
windows: venv\Scripts\activate
mac/linux: source venv/bin/activate
Install the requirements
pip install -r requirements.txt
Run it
python app.py
go to http://127.0.0.1:5000 in your browser, thats it

the database gets created automatically the first time you run it (instance/trekking.db), you dont have to do anything manually for that, its all done through code like it says in the problem statement.

Admin login

Since admin isnt supposed to register, i made it auto-create an admin account when app starts for the first time. login with:

>>>email: admin@trekapp.com password: Admin@123

(should probably change this if this was a real app lol, but its fine for the demo)

Folder structure
app.py            <- main file, run this
models.py         <- database tables (User, Trek, Booking)
core/
  config.py       <- settings
  extensions.py   <- flask-login and db setup
  decorators.py   <- the role_required thing for checking admin/staff/user
blueprints/
  auth.py         <- login/register/logout
  admin.py        <- all admin routes
  staff.py        <- all staff routes  
  user.py         <- all user/trekker routes
templates/        <- all the html files
static/           <- css


##Some rules I added

cant book a trek if its not "Open" status or if slots are full
staff cant see/edit other staffs treks, only their own assigned ones
blacklisted users/staff cant login at all
Notes
used AI (Claude) to help scaffold this project and for debugging along the way, but went through the code myself and understand how it works, can explain/modify it if asked
didnt use JS for any of the core stuff as mentioned in the requirements, its all flask + jinja + bootstrap
tested it manually by clicking through all the flows (admin approving staff, assigning treks, booking, cancelling etc) to make sure nothing breaks